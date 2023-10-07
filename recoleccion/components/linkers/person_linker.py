from typing import List, Tuple
from dedupe import Gazetteer
import pandas as pd
from datetime import date

# Project
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import unidecode_text
from recoleccion.models import Person
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.models import PersonLinking
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


class PersonLinker(Linker):
    fields = [
        {"field": "name", "type": "String"},
        {"field": "last_name", "type": "String"},
    ]

    def __init__(self):
        self.logger = CustomLogger(self.__class__.__name__)
        self.gazetteer = Gazetteer(self.fields)
        self.canonical_data = self.get_canonical_data()

    def get_canonical_data(
        self,
    ):
        canonical_data = pd.DataFrame(
            map(lambda x: (x.name, x.last_name, x.id), Person.objects.all()), columns=["name", "last_name", "id"]
        )
        canonical_data[["name", "last_name"]] = canonical_data[["name", "last_name"]].applymap(
            lambda x: unidecode_text(x)
        )
        canonical_data = canonical_data.to_dict(orient="index")
        return canonical_data

    def get_messy_data(self, original_data: pd.DataFrame):
        messy_data = original_data.copy()
        messy_data[["name", "last_name"]] = messy_data[["name", "last_name"]].applymap(lambda x: unidecode_text(x))
        messy_data = self._convert_dates_to_str(messy_data)
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def link_persons(self, data: pd.DataFrame):
        self.logger.info(f"Linking {len(data)} persons...")
        try:
            linked_persons = 0
            messy_data: dict = self.get_messy_data(data)
            manually_linked_data, undefined_data = self.apply_manual_linking(messy_data)
            self.logger.info(f"Manually decided on {manually_linked_data.shape[0]} parties")
            undefined_df = pd.DataFrame.from_dict(undefined_data, orient="index")
            try:
                self.train(messy_data)
            except IncompatibleLinkingDatasets as e:
                undefined_df["party_id"] = None
                return self.merge_dataframes(manually_linked_data, undefined_df)
            certain, _ = self.classify(undefined_data)
            mapping = [None for x in range(undefined_df.shape[0])]
            for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
                canonical_data_id = self.canonical_data[canonical_data_index]["id"]
                mapping[messy_data_index] = canonical_data_id
                linked_persons += 1

            undefined_df["person_id"] = mapping
            self.logger.info(f"Linked {linked_persons} persons")
            unlinked_persons = undefined_df["person_id"].isnull().sum()
            self.logger.info(f"{unlinked_persons} persons remain unlinked")
        except ValueError as e:  # TODO: creo que esto se puede sacar
            if "second dataset is empty" in str(e):  # Shouldn't be an error, just means that there are no matches
                undefined_df["person_id"] = None
                self.logger.info("Linked 0 persons")
            else:
                raise e
        total_data = pd.concat([manually_linked_data, undefined_df])
        total_data = total_data.reset_index(drop=True)
        return total_data

    def _convert_dates_to_str(self, data: pd.DataFrame) -> pd.DataFrame:
        # Convert datetime
        for datetime_column in data.select_dtypes(include=["datetime", "datetimetz"]).columns:
            data[datetime_column] = data[datetime_column].dt.strftime("%Y-%m-%d")

        # Convert date
        for date_column in self._get_date_cols(data):
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
        return record_1["name"] == record_2["name"] and record_1["last_name"] == record_2["last_name"]

    def save_linking_decision(self, person_id, messy_name, canonical_name):
        if person_id < 0:
            decision = LinkingDecisions.DENIED
        else:
            decision = LinkingDecisions.APPROVED
        person_id = person_id if person_id > 0 else None
        PersonLinking.objects.create(
            person_id=person_id, full_name=messy_name, compared_against=canonical_name, decision=decision
        )

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["name"] = record["name"]
        new_record["last_name"] = record["last_name"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def get_record_id(self, record: dict):
        return record["id"]

    def approved_linking(self, canonical_name: str, messy_name: str) -> Tuple[bool, int]:
        person_link = PersonLinking.objects.filter(full_name=messy_name, compared_against=canonical_name).first()
        if person_link:
            if person_link.decision == LinkingDecisions.APPROVED:
                return True, person_link.person_id
        return False, None

    def rejected_linking(self, canonical_name: str, messy_name: str) -> bool:
        person_link = PersonLinking.objects.filter(full_name=messy_name, compared_against=canonical_name).first()
        if person_link:
            if person_link.decision == LinkingDecisions.DENIED:
                return True
        return False

    def apply_manual_linking(self, messy_data: dict) -> Tuple[pd.DataFrame, dict]:
        """
        Applies previously made decisions to the linking process. To be used before actually using the Gazetteer.
        Receives messy_data, and links it using previously saved decisions
        Returns approved_data, rejected_data and undefined_data
        """
        approved_data, rejected_data = [], []
        undefined_data = {}
        canonical_data: dict = self.get_canonical_data()

        for messy_index, messy_record in messy_data.items():
            messy_full_name = messy_record["name"] + " " + messy_record["last_name"]
            decision_found = False
            for canonical_index, canonical_record in canonical_data.items():
                canonical_full_name = canonical_record["name"] + " " + canonical_record["last_name"]
                is_approved, person_id = self.approved_linking(canonical_full_name, messy_full_name)
                if is_approved:
                    messy_record: dict = messy_data[messy_index]
                    messy_record["person_id"] = person_id
                    approved_data.append(messy_record)
                    decision_found = True
                    break
                elif self.rejected_linking(canonical_full_name, messy_full_name):
                    messy_record: dict = messy_data[messy_index]
                    messy_record["person_id"] = None
                    rejected_data.append(messy_record)
                    decision_found = True
                    break
            if not decision_found:
                messy_record = messy_data[messy_index]
                undefined_data[messy_index] = messy_record
        manually_linked_data: pd.DataFrame = self.assemble_manually_linked_data(approved_data, rejected_data)
        return manually_linked_data, undefined_data
