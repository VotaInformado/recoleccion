import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource, Resource
from recoleccion.components.utils import clean_text_formatting


class DeputyHistory(Resource):
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

    def clean_data(self, data):
        data = self.get_and_rename_relevant_columns(data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True)

        return data


class DeputySource(DataSource):
    base_url = "https://datos.hcdn.gob.ar:443/api/3"
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
                if resource["format"] == "CSV": #Faltaría manejo de errores y sino probar con JSON
                    resources.append(Resource(resource["name"], resource["id"]))
        return resources

    @classmethod
    def get_resource(cls, resource: DeputyHistory):
        url = f"{cls.base_url}/action/resource_show?id={resource.key}"
        response = requests.get(url)
        resource_url = response.json()["result"]["url"]
        return resource.clean_data(pd.read_csv(resource_url, sep=","))
