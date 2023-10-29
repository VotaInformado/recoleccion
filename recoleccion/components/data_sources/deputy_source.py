import io
import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.components.utils import clean_text_formatting
from recoleccion.utils.enums.provinces import Provinces


class DeputiesHistory(DataSource):
    url = "https://datos.hcdn.gob.ar:443/dataset/a80e0fa7-d73a-4ed1-9dec-80465e368951/resource/169de2eb-465f-4007-a4c2-39a5ba4c0df3/download/diputados2.1.csv"
    column_mappings = {  # cambiaron de nombre las columnas se ve
        "id": "deputy_id",
        "nombre": "name",
        "apellido": "last_name",
        "distrito": "district",
        "bloque": "party",
        "inicio": "start_of_term",
        "cese": "end_of_term",
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
        csv_data = response.content
        df = pd.read_csv(io.StringIO(csv_data.decode("utf-8")))
        return df

    @classmethod
    def get_data(cls):
        raw_data: pd.DataFrame = cls.get_raw_data()
        data = cls.get_and_rename_relevant_columns(raw_data)
        for column in ["name", "last_name", "district", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column]).dt.date

        try:
            data["district"] = data["district"].map(lambda x: Provinces.get_choice(x))
        except ValueError as e:
            cls.logger.warning(f"District not found in {cls.__class__.__name__}: {e}")

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
            data[column] = pd.to_datetime(data[column], format="mixed").dt.date
        data["is_active"] = True

        try:
            data["district"] = data["district"].map(lambda x: Provinces.get_choice(x))
        except ValueError as e:
            cls.logger.warning(f"District not found in {cls.__class__.__name__}: {e}")
        return data
