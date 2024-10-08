from typing import Tuple
from dedupe import Gazetteer
import pandas as pd
from django.apps import apps
from collections import OrderedDict


# Project
from recoleccion.models.linking import DENIED_INDICATOR
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import unidecode_text
from recoleccion.models import PartyLinkingDecision
from recoleccion.models.party import PartyDenomination
import logging
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


class PartyLinker(Linker):
    fields = [
        {"field": "denomination", "type": "String"},
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gazetteer = Gazetteer(self.fields)
        self.canonical_data = self.get_canonical_data()
        self.denomination_mapping = {}

    def get_canonical_data(self) -> dict:
        denominations = PartyDenomination.objects.all().order_by("id")
        canonical_data = pd.DataFrame(
            map(lambda x: (x.denomination, x.party.id), denominations),
            columns=["denomination", "party_id"],
        )
        canonical_data[["denomination"]] = canonical_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        canonical_data = canonical_data.to_dict(orient="index")
        return OrderedDict(canonical_data)

    def convert_denomination(self, original_denomination: str) -> str:
        new_denomination = unidecode_text(original_denomination)
        self.denomination_mapping[new_denomination] = original_denomination
        return new_denomination

    def restore_denomination(self, new_denomination: str) -> str:
        return self.denomination_mapping[new_denomination]

    def get_messy_data(self, original_data: pd.DataFrame, save_original_denominations) -> dict:
        messy_data = original_data.copy()
        messy_data = messy_data.rename(columns={"party_name": "denomination", "id": "record_id"})
        if save_original_denominations:
            messy_data[["denomination"]] = messy_data[["denomination"]].applymap(lambda x: self.convert_denomination(x))
            self.logger.info(f"Converted {len(self.denomination_mapping)} denominations")
        else:
            messy_data[["denomination"]] = messy_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def load_exact_matches(self, messy_data: dict) -> Tuple[pd.DataFrame, dict]:
        """
        First we make sure that exact matches are linked together
        Returns:
            - A DF with columns: denomination, record_id, party_id
            - A dict with unmatched data (with the same format of messy_data)
        """
        party_denominations = PartyDenomination.objects.all()
        denominations_info = {pd.denomination.lower(): pd.party_id for pd in party_denominations}
        matched_data, unmatched_data = {}, {}
        md_index = ud_index = 0
        for id, messy_record in messy_data.items():
            messy_denomination = messy_record["denomination"].lower()
            if messy_denomination in denominations_info:
                matched_data[md_index] = messy_record
                matched_data[md_index]["party_id"] = denominations_info[messy_denomination]
                md_index += 1
            else:
                unmatched_data[ud_index] = messy_record
                ud_index += 1
        matched_df = pd.DataFrame.from_dict(matched_data, orient="index")
        return matched_df, unmatched_data

    def create_certain_mapping(self, undefined_df: pd.DataFrame, certain_matches: list) -> list:
        certain_mapping = [None for x in range(undefined_df.shape[0])]
        for messy_data_index, canonical_data_index in certain_matches:
            canonical_data_id = self.canonical_data[canonical_data_index]["party_id"]
            certain_mapping[messy_data_index] = canonical_data_id
        self.logger.info(f"Linked {len(certain_matches)} parties")
        return certain_mapping

    def create_dubious_mapping(self, undefined_df: pd.DataFrame, dubious_matches: list) -> list:
        dubious_mapping = [None for x in range(undefined_df.shape[0])]
        for messy_data_index, canonical_data_index, linking_id in dubious_matches:
            dubious_mapping[messy_data_index] = linking_id
        self.logger.info(f"Linked {len(dubious_matches)} parties")
        return dubious_mapping

    def remove_linked_data(self, undefined_df: pd.DataFrame, linked_indexes: list) -> pd.DataFrame:
        undefined_df = undefined_df.drop(index=linked_indexes)
        return undefined_df

    def link_parties(self, data: pd.DataFrame, save_original_denominations=False) -> pd.DataFrame:
        """
        Receives a DF with columns: denomination, record_id
        Returns a DF with columns: denomination, record_id, party_id
        """
        self.logger.info(f"Linking {len(data)} parties...")
        data = data.rename(columns={"id": "record_id"})
        try:
            messy_data: dict = self.get_messy_data(data, save_original_denominations)
            exactly_matched_data, undefined_data = self.load_exact_matches(messy_data)
            self.logger.info(f"Exactly matched {exactly_matched_data.shape[0]} parties")
            undefined_data = self.reset_index(undefined_data)
            undefined_df = pd.DataFrame.from_dict(undefined_data, orient="index")
            try:
                self.train(undefined_data)
            except IncompatibleLinkingDatasets as e:
                undefined_df["party_id"] = None
                merged_df = self.merge_dataframes(exactly_matched_data, undefined_df)
                if save_original_denominations:
                    merged_df["denomination"] = merged_df["denomination"].apply(lambda x: self.restore_denomination(x))
                return merged_df
            certain, dubious, distinct = self.classify(undefined_data)
            self.logger.info(f"{len(dubious)} records entered in the dubious range")
            certain_mapping = self.create_certain_mapping(undefined_df, certain)
            undefined_df["party_id"] = certain_mapping
            dubious_mapping = self.create_dubious_mapping(undefined_df, dubious)
            undefined_df["linking_id"] = dubious_mapping
            self.logger.info(f"{len(distinct)} parties will not be linked")
        except ValueError as e:
            if "first dataset is empty" in str(e) or "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                undefined_df["party_id"] = None
                self.logger.info("Linked 0 parties")
            else:
                raise e
        merged_df = self.merge_dataframes(exactly_matched_data, undefined_df)
        if save_original_denominations:
            merged_df["denomination"] = merged_df["denomination"].apply(lambda x: self.restore_denomination(x))
        return merged_df

    def are_the_same_record(self, record_1, record_2):
        return record_1["denomination"] == record_2["denomination"]

    def _save_pending_decisions(self, identical_pairs):
        pass

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["denomination"] = record["denomination"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def get_record_id(self, record: dict):
        return record["party_id"]

    def approved_linking(self, canonical_id: int, messy_denomination: str) -> Tuple[bool, int]:
        party_link = PartyLinkingDecision.objects.filter(
            messy_denomination__iexact=messy_denomination, party_id=canonical_id
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisionOptions.APPROVED:
                return True, party_link.party_id
        return False, None

    def rejected_linking(self, canonical_id: int, messy_denomination: str) -> bool:
        party_link = PartyLinkingDecision.objects.filter(
            messy_denomination__iexact=messy_denomination, party_id=canonical_id
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisionOptions.DENIED:
                return True
        return False

    def _set_record_id(self, party_denomination_id: int, record_linking_id: int):
        party_id = PartyDenomination.objects.get(id=party_denomination_id).party_id
        classes = ["Authorship", "DeputySeat", "SenateSeat", "Vote"]
        for each_class in classes:
            model = apps.get_model("recoleccion", each_class)
            matches = model.objects.filter(linking_id=record_linking_id)
            matches.update(party_id=party_id)
        canonical_name = PartyDenomination.objects.get(
            party_id=party_id
        ).denomination  # OJO: Denomination id != party id

    def get_or_save_pending_linking_decision(
        self, canonical_record: dict, messy_record: dict
    ) -> Tuple[PartyLinkingDecision, bool]:
        """
        Receives a canonical record and a messy record
        Checks if there is a pending decision for the pair, using canonical_record_id and messy_denomination
        If there is one, returns the decision and False
        If there isn't, creates a new decision and returns it with True
        """
        party_id = self.get_record_id(canonical_record)
        messy_denomination = messy_record["denomination"]
        existing_decision = PartyLinkingDecision.objects.filter(
            party_id=party_id, messy_denomination=messy_denomination
        ).first()
        if existing_decision:
            return existing_decision, False
        new_decision = PartyLinkingDecision.objects.create(party_id=party_id, messy_denomination=messy_denomination)
        return new_decision, True

    def get_linking_key(self, canonical_data_index: int, messy_record: dict):
        messy_denomination = messy_record["denomination"]
        return (canonical_data_index, messy_denomination)
