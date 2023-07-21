import requests
import pandas as pd
from bs4 import BeautifulSoup

# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.components.utils import clean_text_formatting


class SenateHistory(DataSource):
    url = "https://www.senado.gob.ar/micrositios/DatosAbiertos/ExportarListadoSenadoresHistorico/json"
    column_mappings = {
        "nombre": "name",
        "apellido": "last_name",
        "provincia": "province",
        "partido politico o alianza": "party",
        "inicio periodo legal": "start_of_term",
        "cese periodo legal": "end_of_term",
    }

    @classmethod
    def get_raw_data(cls) -> pd.DataFrame:
        response = requests.get(cls.url)
        data = response.json()["table"]["rows"]
        return pd.DataFrame(data)

    @classmethod
    def get_data(cls):
        data = cls.get_raw_data()
        data.columns = [column.lower() for column in data.columns]
        data[["apellido", "nombre"]] = data["senador"].str.split(",", n=1, expand=True)
        data = cls.get_and_rename_relevant_columns(data)
        # Reemplazo los DNI en 0 por None para que no explote por duplicado
        data = data.replace(0, None)
        for column in ["name", "last_name", "province", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True).dt.date
        return data


class CurrentSenate(DataSource):
    url = "https://www.senado.gob.ar/micrositios/DatosAbiertos/ExportarListadoSenadores/json"
    column_mappings = {
        "nombre": "name",
        "apellido": "last_name",
        "provincia": "province",
        "partido o alianza": "party",
        "d_legal": "start_of_term",
        "c_legal": "end_of_term",
        "telefono": "phone",
    }
    correct_columns = {"twitter", "facebook", "instagram", "youtube", "email"}

    @classmethod
    def get_raw_data(cls) -> pd.DataFrame:
        response = requests.get(cls.url)
        data = response.json()["table"]["rows"]
        return pd.DataFrame(data)

    @classmethod
    def get_data(cls):
        raw_data = cls.get_raw_data()
        data = cls.get_and_rename_relevant_columns(raw_data)
        # Reemplazo los DNI en 0 por None para que no explote por duplicado
        data = data.replace(0, None)
        for column in ["name", "last_name", "province", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True).dt.date
        data["is_active"] = True
        return data
