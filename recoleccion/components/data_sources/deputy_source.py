import io
import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource, Resource
from recoleccion.components.utils import clean_text_formatting


class DeputyHistory(Resource):
    base_url = "https://datos.hcdn.gob.ar:443/api/3"
    name = "DeputyHistory"
    key = "169de2eb-465f-4007-a4c2-39a5ba4c0df3"
    column_mappings = {
        "diputado_id": "deputy_id",
        "diputado_nombre": "name",
        "diputado_apellido": "last_name",
        # "DIPUTADO_GENERO": "gender",
        "diputado_distrito": "district",
        "diputado_bloque": "party",
        "mandato_inicio": "start_of_term",
        "mandato_fin": "end_of_term",
    }

    def get_raw_data(self):
        url = f"{self.base_url}/action/resource_show?id={self.key}"
        response = requests.get(url)
        resource_url = response.json()["result"]["url"]
        data = pd.read_csv(resource_url)
        return data

    def get_clean_data(self):
        raw_data: pd.DataFrame = self.get_raw_data()
        data = self.get_and_rename_relevant_columns(raw_data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True)
        return data


class CurrentDeputies(DeputyHistory):
    """There isn't actually a resource for current deputies.
    We get the historic data and filter the ones that are current
    """

    column_mappings = {
        "nombre": "name",
        "apellido": "last_name",
        # "DIPUTADO_GENERO": "gender",
        "distrito": "district",
        "bloque": "party",
        "iniciamandato": "start_of_term",
        "finalizamandato": "end_of_term",
    }

    FILE_PATH = "recoleccion/files/diputados.csv"

    def get_raw_data(self):
        return pd.read_csv(self.FILE_PATH)

    def get_clean_data(self):
        raw_data = self.get_raw_data()
        data = self.get_and_rename_relevant_columns(raw_data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], format="mixed")
        data["is_active"] = True
        return data


class LawSummarySource(Resource):
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

    def get_clean_data(self):
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


class DeputySource(DataSource):
    resources = [
        DeputyHistory(),
    ]

    @classmethod
    def get_resources(cls):
        url = f"{cls.base_url}/action/current_package_list_with_resources"
        response = requests.request("GET", url)
        resources = []
        for dataset in response.json()["result"]:
            for resource in dataset["resources"]:
                if resource["format"] == "CSV":  # Faltaría manejo de errores y sino probar con JSON
                    resources.append(Resource(resource["name"], resource["id"]))
        return resources

    @classmethod
    def get_resource(cls, resource: DeputyHistory):
        return resource.get_clean_data()
