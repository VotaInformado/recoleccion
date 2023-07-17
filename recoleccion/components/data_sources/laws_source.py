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
        "decreto_promulgacion": "decree",
        "veto": "veto",
        "expediente_inicial": "initial_file",
    }

    def get_publication_data(self):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=cbf78f72-1098-4e84-99e7-695d6d65a02a&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    def get_laws_data(self):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=3dc4e8e1-2148-4bf0-b9c9-f19cafc6ff8e&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    def get_sanction_data(self):
        url = "https://datos.hcdn.gob.ar/dataset/5b1d2f38-e23f-412c-a286-02ab9dcf6082/resource/68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98/download/leyes_sancionadas1.5.csv"
        response = requests.get(url)
        data = response.content
        df = pd.read_csv(io.StringIO(data.decode("utf-8")))
        reduced_df = df[["ley", "expediente_inicial"]]
        return pd.DataFrame(reduced_df)

    def extract_dates_from_datetimes(self, datetime_str):
        key_index = datetime_str.find("T")
        return datetime_str[:key_index]

    def get_data(self):
        laws_data = self.get_laws_data()
        self.logger.info(f"Base laws data size: {len(laws_data)}")
        publication_data = self.get_publication_data()
        self.logger.info(f"Publication data size: {len(publication_data)}")
        data = laws_data.merge(publication_data, on="ley", how="left")
        self.logger.info(f"First merge data size: {len(data)}")
        sanction_data = self.get_sanction_data()
        self.logger.info(f"Sanction data size: {len(sanction_data)}")
        data = data.merge(sanction_data, on="ley", how="left")
        self.logger.info(f"Second merge data size: {len(data)}")
        data = self.get_and_rename_relevant_columns(data)
        data["publication_date"] = data["publication_date"].map(self.extract_dates_from_datetimes)
        return data


class LawProjectSource(DataSource):
    column_mappings = {
        "proyecto_id": "project_id",
        "proyecto_titulo": "title",
        "publicacion_fecha": "publication_date",
        "camara_origen": "origin_chamber",
        "expediente_diputados": "deputy_file_id",
        "expediente_senado": "senate_file_id",
        "proyecto_tipo": "project_type",
    }

    def get_data(self):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&limit=1000000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        raw_df = pd.DataFrame(data)
        # first we filter all those projects with type different from "Ley"
        df = raw_df[raw_df["proyecto_tipo"] == "Ley"]
        import pdb; pdb.set_trace()
        df = df.drop(columns=["_id", "proyecto_texto", "proyecto_texto_pdf"])
