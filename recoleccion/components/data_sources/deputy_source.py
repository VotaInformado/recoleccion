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
