import io
import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource


class LawSource(DataSource):
    column_mappings = {
        "ley": "law_number",
        "titulo": "title",
        "sumario": "summary",
        "referencias": "tags",
        "fecha_publicacion": "publication_date",
        "decreto_promulgacion": "associated_decree",
        "veto": "veto",
        "expediente_inicial": "initial_file",
        "proyecto_id": "project_id",
    }

    @classmethod
    def get_publication_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=cbf78f72-1098-4e84-99e7-695d6d65a02a&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    @classmethod
    def get_laws_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=3dc4e8e1-2148-4bf0-b9c9-f19cafc6ff8e&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    @classmethod
    def get_sanction_data(cls):
        url = "https://datos.hcdn.gob.ar/dataset/5b1d2f38-e23f-412c-a286-02ab9dcf6082/resource/68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98/download/leyes_sancionadas1.5.csv"
        response = requests.get(url)
        data = response.content
        df = pd.read_csv(io.StringIO(data.decode("utf-8")))
        reduced_df = df[["ley", "expediente_inicial", "proyecto-id"]]
        return pd.DataFrame(reduced_df)

    @classmethod
    def extract_dates_from_datetimes(cls, datetime_str):
        key_index = datetime_str.find("T")
        return datetime_str[:key_index]

    @classmethod
    def get_data(cls):
        laws_data = cls.get_laws_data()
        cls.logger.info(f"Base laws data size: {len(laws_data)}")
        publication_data = cls.get_publication_data()
        cls.logger.info(f"Publication data size: {len(publication_data)}")
        data = laws_data.merge(publication_data, on="ley", how="left")
        cls.logger.info(f"First merge data size: {len(data)}")
        sanction_data = cls.get_sanction_data()
        cls.logger.info(f"Sanction data size: {len(sanction_data)}")
        data = data.merge(sanction_data, on="ley", how="left")
        cls.logger.info(f"Second merge data size: {len(data)}")
        data = cls.get_and_rename_relevant_columns(data)
        data["publication_date"] = data["publication_date"].map(cls.extract_dates_from_datetimes)
        return data
    

