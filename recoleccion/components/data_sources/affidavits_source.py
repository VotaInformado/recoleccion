import logging
import requests
import re
import pandas as pd
import zipfile
import io

# Project
from recoleccion.components.data_sources.data_source import DataSource
from recoleccion.utils.enums.affidavit import AffidevitType
from recoleccion.components.utils import unidecode_text


logger = logging.getLogger(__name__)


class AffidavitsSource(DataSource):
    files_content = {}
    session = requests.Session()
    ZIP_FOLDER_LOCAL_PATH = "recoleccion/files/declaraciones-juradas.zip"
    ZIP_FOLDER_URL = "http://datos.jus.gob.ar/dataset/4680199f-6234-4262-8a2a-8f7993bf784d/resource/43c3cf87-b78f-4dd5-a821-686999d42231/download/declaraciones-juradas-2022.zip"
    column_mappings = {
        "tipo_declaracion_jurada_id": "affidavit_type",
        "funcionario_apellido_nombre": "full_name",
        "anio": "year",
        "total_bienes_final": "value",
        # "total_bienes_inicio": "initial_value",
    }

    @classmethod
    def _normalize_text(cls, text: str):
        return unidecode_text(text.lower())

    @classmethod
    def _meets_filter_condition(cls, x: str):
        return "camara de diputados" in x or "honorable senado" in x

    @classmethod
    def _filter_legislators(cls, raw_data: pd.DataFrame):
        # we filter first if they don't have "organismo" value
        raw_data = raw_data.dropna(subset=["organismo", "tipo_declaracion_jurada_id"])
        # sin tipo de declaracion jurada, no podemos determinar el año que le asignamos
        raw_data.loc[:, "organismo"] = raw_data["organismo"].apply(lambda x: cls._normalize_text(x))
        mask = raw_data["organismo"].apply(lambda x: cls._meets_filter_condition(x))
        filtered_data = raw_data[mask]
        return filtered_data

    @classmethod
    def _get_year_info(cls, year: int) -> pd.DataFrame:
        file_content = cls.files_content.get(year)
        if not file_content:
            logger.info(f"No data found for year {year}")
            return pd.DataFrame()
        raw_data = pd.read_csv(io.BytesIO(file_content))
        logger.info(f"Received {len(raw_data)} records for year {year}")
        year_data = cls._filter_legislators(raw_data)
        logger.info(f"Filtered to {len(year_data)} records for year {year}")
        year_data = cls.get_and_rename_relevant_columns(year_data)
        year_data["affidavit_type"] = year_data["affidavit_type"].apply(lambda x: AffidevitType.translate_raw_value(x))
        return year_data

    @classmethod
    def get_data(cls, year: int):
        year_info = cls._get_year_info(year)
        year_data = pd.DataFrame(year_info)
        if year_data.empty:
            return year_data
        year_data["source"] = f"Affidavit-{year}"
        return year_data

    @classmethod
    def _is_correct_file(cls, file_name: str):
        # Returns true if the file is a general affidavit file and not a particular one (debts, goods, etc)
        return "bienes" not in file_name and "familiar" not in file_name and "deudas" not in file_name

    @classmethod
    def _fetch_raw_data(cls) -> bytes:
        req = cls.session.get(cls.ZIP_FOLDER_URL)
        return req.content

    @classmethod
    def _fetch_raw_data_alt(cls) -> bytes:
        with open(cls.ZIP_FOLDER_LOCAL_PATH, "rb") as zip_file:
            content = zip_file.read()
        return content

    @classmethod
    def load_data(cls) -> None:
        # Loads each file content into the class variable files_content
        raw_data: bytes = cls._fetch_raw_data_alt()
        year_pattern = re.compile(r"-(\d{4})-")
        with zipfile.ZipFile(io.BytesIO(raw_data), "r") as zip_ref:
            extracted_files = zip_ref.namelist()
            filtered_files = [file_name for file_name in extracted_files if cls._is_correct_file(file_name)]
            for file_name in filtered_files:
                with zip_ref.open(file_name) as file:
                    file_year = int(year_pattern.search(file_name).group(1))
                    file_content = file.read()
                    cls.files_content[file_year] = file_content
