from typing import List
from dedupe import Gazetteer
import pandas as pd
from datetime import date

# Project
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
            messy_data = self.get_messy_data(data)
            self.train(messy_data)
            certain, _ = self.classify(messy_data)
            mapping = [None for x in range(data.shape[0])]
            for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
                canonical_data_id = self.canonical_data[canonical_data_index]["id"]
                mapping[messy_data_index] = canonical_data_id
                linked_persons += 1

            data["person_id"] = mapping
            self.logger.info(f"Linked {linked_persons} persons")
            unlinked_persons = data["person_id"].isnull().sum()
            self.logger.info(f"{unlinked_persons} persons remain unlinked")
        except ValueError as e:
            if "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                data["person_id"] = None
                self.logger.info("Linked 0 persons")
            else:
                raise e
        return data

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

    def load_linking(self, person_id, messy_name, canonical_name):
        if person_id < 0:
            decision = LinkingDecisions.DENIED
        else:
            decision = LinkingDecisions.APPROVED
        PersonLinking.objects.create(
            person_id=person_id, full_name=messy_name, compared_against=canonical_name, decision=decision
        )

    def get_record_id(self, messy_data, index_pair):
        messy_data_index, canonical_data_index = index_pair
        messy_name = messy_data[messy_data_index]["name"] + " " + messy_data[messy_data_index]["last_name"]
        canonical_name = (
            self.canonical_data[canonical_data_index]["name"]
            + " "
            + self.canonical_data[canonical_data_index]["last_name"]
        )
        # gets person_id from messy_name. If not found, returns 0, if it is found but not approved, returns -1
        person_link = PersonLinking.objects.filter(full_name=messy_name, compared_against=canonical_name).first()
        if not person_link:
            return 0
        return person_link.person.pk  # will return -1 if denied

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["name"] = record["name"]
        new_record["last_name"] = record["last_name"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record
