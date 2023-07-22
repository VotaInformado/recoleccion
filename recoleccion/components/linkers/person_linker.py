from typing import List
from dedupe import Gazetteer
import pandas as pd
from datetime import date

# Project
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import unidecode_text
from recoleccion.models import Person


class PersonLinker(Linker):
    fields = [
        {"field": "name", "type": "String"},
        {"field": "last_name", "type": "String"},
    ]

    def __init__(self):
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
        try:
            messy_data = self.get_messy_data(data)
            self.train(messy_data)
            certain, _ = self.classify(messy_data)
            mapping = [None for x in range(data.shape[0])]
            for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
                # canonical_data_id = (
                #     canonical_data_index + 1
                # )  # Don't know why it's necessary maybe: `canonical_data[canonical_data_index].id`?
                canonical_data_id = self.canonical_data[canonical_data_index]["id"]
                mapping[messy_data_index] = canonical_data_id

            data["person_id"] = mapping
        except ValueError as e:
            if "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                data["person_id"] = None
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
