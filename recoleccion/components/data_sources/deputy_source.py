import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.components.utils import clean_text_formatting


class DeputyHistory(DataSource):
    url = "https://datos.hcdn.gob.ar:443/api/3/action/resource_show?id=169de2eb-465f-4007-a4c2-39a5ba4c0df3"
    column_mappings = {
        "diputado_id": "deputy_id",
        "diputado_nombre": "name",
        "diputado_apellido": "last_name",
        "diputado_distrito": "district",
        "diputado_bloque": "party",
        "mandato_inicio": "start_of_term",
        "mandato_fin": "end_of_term",
    }

    @classmethod
    def get_raw_data(cls):
        response = requests.get(cls.url)
        resource_url = response.json()["result"]["url"]
        data = pd.read_csv(resource_url)
        return data

    @classmethod
    def get_data(cls):
        raw_data: pd.DataFrame = cls.get_raw_data()
        data = cls.get_and_rename_relevant_columns(raw_data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True)
        return data


class CurrentDeputies(DataSource):
    """There isn't actually a resource for current deputies.
    We get the historic data and filter the ones that are current
    """

    file_path = "recoleccion/files/diputados.csv"

    column_mappings = {
        "nombre": "name",
        "apellido": "last_name",
        "distrito": "district",
        "bloque": "party",
        "iniciamandato": "start_of_term",
        "finalizamandato": "end_of_term",
    }

    @classmethod
    def get_raw_data(cls):
        return pd.read_csv(cls.file_path)

    @classmethod
    def get_data(cls):
        raw_data = cls.get_raw_data()
        data = cls.get_and_rename_relevant_columns(raw_data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], format="mixed")
        data["is_active"] = True
        return data
