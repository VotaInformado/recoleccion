from collections import defaultdict, OrderedDict
from datetime import date
from dedupe import Gazetteer
from typing import List, Tuple
import pandas as pd
import datetime as dt
from uuid import UUID

# Project
from recoleccion.models.linking import DENIED_INDICATOR
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import normalize_name, unidecode_text
from recoleccion.models import Person
import logging
from recoleccion.models import PersonLinkingDecision
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


class PersonLinker(Linker):
    fields = [
        {"field": "full_name", "type": "String"},
    ]

    def __init__(self, use_alternative_names=False):
        self.logger = logging.getLogger(__name__)
        self.gazetteer = Gazetteer(self.fields)
        self.use_alternative_names = use_alternative_names
        self.canonical_data = self.get_canonical_data()

    def get_canonical_data(self) -> dict:
        if self.use_alternative_names or True:
            return self._get_canonical_data_alternative_format()

    def _get_canonical_data(self) -> dict:
        all_persons = Person.objects.all().order_by("id")
        canonical_data = pd.DataFrame(
            map(lambda x: (x.name, x.last_name, x.id), all_persons), columns=["name", "last_name", "id"]
        )
        canonical_data[["name", "last_name"]] = canonical_data[["name", "last_name"]].applymap(
            lambda x: normalize_name(x)
        )
        canonical_data = canonical_data.to_dict(orient="index")
        return OrderedDict(canonical_data)

    def _get_canonical_data_alternative_format(self) -> dict:
        all_persons = Person.objects.all().order_by("id")
        canonical_data = pd.DataFrame(
            map(lambda x: (x.name, x.last_name, x.id), all_persons), columns=["name", "last_name", "id"]
        )
        canonical_data[["name", "last_name"]] = canonical_data[["name", "last_name"]].applymap(
            lambda x: normalize_name(x)
        )
        canonical_data["full_name"] = canonical_data["last_name"] + " " + canonical_data["name"]
        canonical_data = canonical_data.drop(columns=["name", "last_name"])
        canonical_data = canonical_data.to_dict(orient="index")
        return OrderedDict(canonical_data)

    def get_messy_data(self, original_data: pd.DataFrame):
        if self.use_alternative_names or True:
            return self._get_messy_data_alternative(original_data)
        return self._get_messy_data(original_data)

    def _get_messy_data(self, original_data: pd.DataFrame):
        messy_data = original_data.copy()
        messy_data[["name", "last_name"]] = messy_data[["name", "last_name"]].applymap(lambda x: normalize_name(x))
        messy_data = self._convert_dates_to_str(messy_data)
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def _get_messy_data_alternative(self, original_data: pd.DataFrame):
        # In this case, we don't have name and last_name because they cannot be splitted (no separator)
        messy_data = original_data.copy()
        if "full_name" in messy_data.columns:
            messy_data["full_name"] = messy_data["full_name"].apply(lambda x: normalize_name(x))
        else:
            messy_data[["name", "last_name"]] = messy_data[["name", "last_name"]].applymap(lambda x: normalize_name(x))
            messy_data["full_name"] = messy_data["last_name"] + " " + messy_data["name"]
        messy_data = self._convert_dates_to_str(messy_data)
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def get_record_full_name(self, record: dict, normalize=True) -> str:
        # Alternative records came with "full_name" instead of "name" and "last_name"
        if "name" in record.keys():
            return self._get_record_full_name(record, normalize)
        return self._get_alternative_record_full_name(record, normalize)

    def _get_record_full_name(self, record: dict, normalize=True) -> str:
        raw_name = record["name"] + " " + record["last_name"]
        if normalize:
            raw_name = raw_name.lower()
            raw_name = unidecode_text(raw_name)
        return raw_name

    def _get_alternative_record_full_name(self, record: dict, normalize=True) -> str:
        raw_name = record["full_name"]
        if normalize:
            raw_name = raw_name.lower()
            raw_name = unidecode_text(raw_name)
        return raw_name

    def load_exact_matches(self, messy_data: dict) -> Tuple[pd.DataFrame, dict]:
        """
        First we make sure that exact matches are linked together
        Returns:
            - A DF with columns: denomination, record_id, party_id
            - A dict with unmatched data (with the same format of messy_data)
        """
        canonical_data = self.get_canonical_data()
        canonical_info = {self.get_record_full_name(record): record["id"] for record in canonical_data.values()}
        matched_data, unmatched_data = {}, {}
        for id, messy_record in messy_data.items():
            messy_full_name = self.get_record_full_name(messy_record)
            if messy_full_name in canonical_info:
                matched_data[id] = messy_record
                matched_data[id]["person_id"] = canonical_info[messy_full_name]
            else:
                unmatched_data[id] = messy_record
        matched_df = pd.DataFrame.from_dict(matched_data, orient="index")
        return matched_df, unmatched_data

    def create_certain_mapping(self, undefined_df: pd.DataFrame, certain_matches: list) -> List[int]:
        certain_mapping = [None for x in range(undefined_df.shape[0])]
        for messy_data_index, canonical_data_index in certain_matches:
            canonical_data_id = self.canonical_data[canonical_data_index]["id"]
            certain_mapping[messy_data_index] = canonical_data_id
        return certain_mapping

    def create_dubious_mapping(self, undefined_df: pd.DataFrame, dubious_matches: list) -> List[UUID]:
        dubious_mapping = [None for x in range(undefined_df.shape[0])]
        for messy_data_index, _, linking_id in dubious_matches:
            dubious_mapping[messy_data_index] = linking_id
        self.logger.info(f"Linked {len(dubious_matches)} persons")
        return dubious_mapping

    def link_persons(self, data: pd.DataFrame, skip_manual_linking=False):
        """
        Receives a DF with columns: name, last_name, district, party, start_of_term, end_of_term, is_active
        Returns a DF with columns: name, last_name, district, party, start_of_term, end_of_term, is_active, person_id, linking_id
        person_id is the id of the linked person if the linking was made, None otherwise
        linking_id is the id of the pending linking decision that has to be made, if linking entered in the dubious range
        """
        self.logger.info(f"Linking {len(data)} persons...")
        try:
            messy_data: dict = self.get_messy_data(data)
            exactly_matched_data, undefined_data = self.load_exact_matches(messy_data)
            undefined_data = self.reset_index(undefined_data)
            undefined_df = pd.DataFrame.from_dict(undefined_data, orient="index")
            self.logger.info(f"Found {exactly_matched_data.shape[0]} exact matches")
            try:
                self.train(messy_data)
            except IncompatibleLinkingDatasets as e:
                undefined_df["party_id"] = None
                return self.merge_dataframes(exactly_matched_data, undefined_df)
            certain, dubious, distinct = self.classify(undefined_data)
            self.logger.info(f"{len(dubious)} records entered in the dubious range")
            certain_mapping = self.create_certain_mapping(undefined_df, certain)
            undefined_df["person_id"] = certain_mapping
            dubious_mapping = self.create_dubious_mapping(undefined_df, dubious)
            undefined_df["linking_id"] = dubious_mapping
            self.logger.info(f"{len(distinct)} persons will not be linked")
        except ValueError as e:  # TODO: creo que esto se puede sacar
            if "first dataset is empty" in str(e) or "second dataset is empty" in str(e):
                undefined_df["person_id"] = None
                self.logger.info("Linked 0 persons")
            else:
                raise e
        return self.merge_dataframes(exactly_matched_data, undefined_df)

    def _convert_dates_to_str(self, data: pd.DataFrame) -> pd.DataFrame:
        # Convert datetime
        for datetime_column in data.select_dtypes(include=["datetime", "datetimetz"]).columns:
            data[datetime_column].fillna(
                dt.datetime.today().date(), inplace=True
            )  # medida temporal (2023-12-21) porque hay diputados sin fecha de ingreso
            data[datetime_column] = data[datetime_column].dt.strftime("%Y-%m-%d")

        # Convert date
        for date_column in self._get_date_cols(data):
            data[date_column].fillna(dt.datetime.today().date(), inplace=True)
            data[date_column] = data[date_column].map(lambda x: x.strftime("%Y-%m-%d"))

        return data

    def _get_date_cols(self, data: pd.DataFrame) -> List[str]:
        date_cols = []
        if data.shape[0] == 0:
            return date_cols

        for col, value in data.iloc[0].items():
            if isinstance(value, date):
                date_cols.append(col)
        return date_cols

    def are_the_same_record(self, record_1, record_2):
        if "name" in record_1 and "name" in record_2:
            return record_1["name"] == record_2["name"] and record_1["last_name"] == record_2["last_name"]
        else:
            return record_1["full_name"] == record_2["full_name"]

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        if "name" in record:
            new_record["name"] = record["name"]
            new_record["last_name"] = record["last_name"]
        else:
            new_record["full_name"] = record["full_name"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def get_record_id(self, record: dict):
        return record["id"]

    def approved_linking(self, canonical_id: int, messy_name: str) -> Tuple[bool, int]:
        person_link = PersonLinkingDecision.objects.filter(messy_name=messy_name, person_id=canonical_id).first()
        if person_link:
            if person_link.decision == LinkingDecisionOptions.APPROVED:
                return True, person_link.person_id
        return False, None

    def rejected_linking(self, canonical_id: int, messy_name: str) -> bool:
        person_link = PersonLinkingDecision.objects.filter(messy_name=messy_name, person_id=canonical_id).first()
        if person_link:
            if person_link.decision == LinkingDecisionOptions.DENIED:
                return True
        return False

    def get_or_save_pending_linking_decision(
        self, canonical_record: dict, messy_record: dict
    ) -> Tuple[PersonLinkingDecision, bool]:
        """
        Receives a canonical record and a messy record
        Checks if there is a pending decision for the pair, using canonical_record_id and messy_denomination
        If there is one, returns the decision and False
        If there isn't, creates a new decision and returns it with True
        """
        person_id = canonical_record["id"]
        if "name" in messy_record:
            messy_name = messy_record["name"] + " " + messy_record["last_name"]
        else:
            messy_name = messy_record["full_name"]
        existing_decision = PersonLinkingDecision.objects.filter(
            person_id=person_id, messy_name=messy_name
        ).first()
        if existing_decision:
            return existing_decision, False
        new_decision = PersonLinkingDecision.objects.create(person_id=person_id, messy_name=messy_name)
        return new_decision, True

    def get_linking_key(self, canonical_data_index: int, messy_record: dict):
        messy_full_name = self.get_record_full_name(messy_record)
        return (canonical_data_index, messy_full_name)
