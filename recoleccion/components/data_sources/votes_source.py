import re
from typing import List
import requests
import pandas as pd

# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.components.utils import capitalize_text, trim_extra_spaces
from recoleccion.utils.enums.project_chambers import ProjectChambers


class DeputyVotesSource(DataSource):
    column_mappings = {
        "expediente": "project_id",
        "diputado_nombre": "diputado_nombre",  # igual después se divide en name y last_name
        "bloque": "party",
        "distrito_nombre": "province",
        "voto": "vote",
        "titulo": "reference_description",
    }

    @classmethod
    def get_legislator_name_and_last_name(cls, original_name: str):
        if not original_name or "NO INCORPORADO" in original_name:
            return None, None
        pattern = r"[A-ZÁÉÍÓÚÜÑ ]+(?=\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]*\b|$)"
        match = re.search(pattern, original_name, re.UNICODE)
        last_name = match.group().strip()
        name = original_name.replace(last_name, "").strip()
        last_name = capitalize_text(last_name)
        name, last_name = trim_extra_spaces(name), trim_extra_spaces(last_name)
        return name, last_name

    @classmethod
    def get_vote_details_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=f86728ed-d4b9-479e-b939-a9841fd6d8d3&limit=1000000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        df = pd.DataFrame(data)
        return df[["acta_id", "diputado_nombre", "bloque", "distrito_nombre", "voto"]]

    @classmethod
    def get_vote_header_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=59c05ba8-ad0a-4d55-803d-20e3fe464d0b&limit=1000000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        df = pd.DataFrame(data)
        return df[["acta_id", "fecha"]]

    @classmethod
    def get_file_info(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=f03e828b-c139-41ad-8063-f77f7ed3e009&limit=10000000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        df = pd.DataFrame(data)
        return df[["acta_id", "expediente", "titulo"]]

    @classmethod
    def add_reference_description(cls, reference_description: str):
        return "" if pd.isnull(reference_description) or not reference_description else reference_description

    @classmethod
    def clean_legislator_name(cls, data: pd.DataFrame) -> pd.DataFrame:
        new_columns: List[tuple] = data["diputado_nombre"].apply(cls.get_legislator_name_and_last_name)
        names, last_names = zip(*new_columns)
        data["name"] = names
        data["last_name"] = last_names  # must be named like this for the linker
        data = data.drop(columns=["diputado_nombre"])
        # now we drop the rows where we don't have a name
        cls.logger.info(f"Data size before dropping rows without name: {len(data)}")
        data = data.dropna(subset=["name", "last_name"])
        return data

    @classmethod
    def clean_data(cls, data: pd.DataFrame) -> pd.DataFrame:
        data = cls.clean_legislator_name(data)
        data = data.reset_index(drop=True)  # If not done, it can bring problems when linking
        cls.logger.info(f"Data size after dropping rows without name: {len(data)}")
        data["reference_description"] = data["reference_description"].apply(cls.add_reference_description)
        return data

    @classmethod
    def get_data(cls):
        vote_details_data = cls.get_vote_details_data()
        cls.logger.info(f"Vote details data size: {len(vote_details_data)}")
        vote_header_data = cls.get_vote_header_data()
        cls.logger.info(f"Vote header data size: {len(vote_header_data)}")
        data = vote_details_data.merge(vote_header_data, on="acta_id", how="left")
        cls.logger.info(f"First merge data size: {len(data)}")
        file_info = cls.get_file_info()
        cls.logger.info(f"File info data size: {len(file_info)}")
        data = data.merge(file_info, on="acta_id", how="left")
        cls.logger.info(f"Second merge data size: {len(data)}")
        data = cls.get_and_rename_relevant_columns(data)
        data = cls.clean_data(data)
        data["source"] = "HCDN"
        data["chamber"] = ProjectChambers.DEPUTIES
        return data
