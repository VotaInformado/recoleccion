import re
import datetime as dt
import time
from typing import List
import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup

# Project
from recoleccion.components.utils import digitize_text
from recoleccion.components.data_sources import DataSource
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.project_status import ProjectStatus


class HCDNLawProjects(DataSource):
    ATTEMPTS = 0
    PROJECT_BASE_URL = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=22b2d52c-7a0e-426b-ac0a-a3326c388ba6&limit=100000000"
    PROJECT_EXTRA_URL = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=daf0e90e-d94f-4186-b7cf-dfad5b6f9369&limit=100000000"

    column_mappings = {
        "expediente_diputados": "deputies_project_id",
        "expediente_senado": "senate_project_id",
        "proyecto_titulo": "title",
        "publicacion_fecha": "publication_date",
        "camara_origen": "origin_chamber",
        "expediente_cabecera": "deputies_header_file",
        "resultado": "status",
    }

    @classmethod
    def clean_origin_chamber(cls, origin_chamber: str) -> ProjectChambers.choices:
        if not origin_chamber:
            return None
        if origin_chamber == "Senado":
            return ProjectChambers.SENATORS
        return ProjectChambers.DEPUTIES

    @classmethod
    def translate_status(cls, status):
        if pd.isnull(status) or not status:
            return None
        status_translation = {
            "APROBADO": ProjectStatus.APPROVED,
            "SANCIONADO": ProjectStatus.APPROVED,
            "MEDIA SANCION": ProjectStatus.HALF_SANCTION,
            "RECHAZADO": ProjectStatus.REJECTED,
            "RETIRADO": ProjectStatus.WITHDRAWN,
        }
        return status_translation[status]

    @classmethod
    def get_projects_base_data(cls) -> pd.DataFrame:
        response = requests.get(cls.PROJECT_BASE_URL)
        data = response.json()["result"]["records"]
        df = pd.DataFrame(data)
        df = df[df["proyecto_tipo"] == "LEY"]
        cls.logger.info(f"Base projects data size: {len(data)}")
        return df

    @classmethod
    def get_projects_extra_data(cls) -> pd.DataFrame:
        response = requests.get(cls.PROJECT_EXTRA_URL)
        data = response.json()["result"]["records"]
        cls.logger.info(f"Extra projects data size: {len(data)}")
        return pd.DataFrame(data)

    @classmethod
    def get_raw_data(cls) -> pd.DataFrame:
        base_data = cls.get_projects_base_data()
        extra_data = cls.get_projects_extra_data()
        return base_data.merge(extra_data, left_on="proyecto_id", right_on="expediente_id", how="left")

    @classmethod
    def clean_project_ids(cls, data: pd.DataFrame) -> pd.DataFrame:
        for column in ["deputies_project_id", "senate_project_id"]:
            data[column] = data[column].apply(lambda x: None if x == "" else x)
        return data

    @classmethod
    def get_data(cls):
        raw_data = cls.get_raw_data()
        data = cls.get_and_rename_relevant_columns(raw_data)
        for column in ["publication_date"]:
            data[column] = pd.to_datetime(data[column]).dt.date
        data = cls.clean_project_ids(data)
        data["status"] = data["status"].apply(cls.translate_status)
        data["origin_chamber"] = data["origin_chamber"].apply(cls.clean_origin_chamber)
        data["source"] = "HCDN"
        cls.logger.info(f"Final data size: {len(data)}")
        return data


class ExternalLawProjectsSource(DataSource):
    base_url = "https://dequesetrata.com.ar/proyectos"

    @classmethod
    def get_raw_data(cls, page: int):
        url = f"{cls.base_url}?page={page}"
        cls.logger.info(f"Requesting url: {url}")
        attempts = 0
        while True:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            print(f"Request failed with status code: {response.status_code}")
            if response.status_code == 404 and attempts < 5:
                attempts += 1
                print(f"Page {page} not found, attempting to retrieve again...")
                time.sleep(1)
                continue
            else:
                return None

    @classmethod
    def retrieve_items(cls, page: int, projects_info=list) -> int:
        added_projects = 0
        page_content = cls.get_raw_data(page)
        if not page_content:
            return added_projects  # should be 0

        soup = BeautifulSoup(page_content, "html.parser")
        items = soup.find_all(class_="itemDocProject")
        for i, item in enumerate(items):
            try:
                project_info = cls.extract_project_info(item.text)
                if project_info:
                    projects_info.append(project_info)
                added_projects += 1
            except Exception as e:
                cls.logger.warning(f"An error occurred at item {i} while extracting project info: {e}")
                continue

        return added_projects

    @classmethod
    def get_project_tile(cls, text):
        title_pattern = r"^\s+(.*?)\s+\n"
        title_match = re.search(title_pattern, text, re.MULTILINE)
        project_title = title_match.group(1) if title_match else None
        return project_title

    @classmethod
    def get_publication_date(cls, text):
        date_pattern = r"el (\d{2}-\d{2}-\d{4})"
        date_match = re.search(date_pattern, text)
        publication_date = date_match.group(1) if date_match else None
        publication_date = cls.clean_publication_date(publication_date)
        return publication_date

    @classmethod
    def get_origin_chamber(cls, text):
        origin_chamber_pattern = r"Senado|Cámara de Diputados"
        origin_chamber_match = re.search(origin_chamber_pattern, text)
        origin_chamber = origin_chamber_match.group() if origin_chamber_match else None
        origin_chamber = cls.clean_origin_chamber(origin_chamber)
        return origin_chamber

    @classmethod
    def get_file_id(cls, text):
        file_id_pattern = r"Expediente:\s+(.*?)\s+"
        file_id_match = re.search(file_id_pattern, text)
        file_id = file_id_match.group(1) if file_id_match else None
        return file_id

    @classmethod
    def get_project_status(cls, text):
        status_pattern = r"Estado:\s+(.*?)\n"
        status_match = re.search(status_pattern, text)
        status = status_match.group(1) if status_match else None
        status = cls.clean_status(status)
        return status

    @classmethod
    def clean_publication_date(cls, date: str) -> dt.datetime:
        if not date:
            return None
        date_format = "%d-%m-%Y"
        return dt.datetime.strptime(date, date_format)

    @classmethod
    def clean_origin_chamber(cls, origin_chamber: str) -> ProjectChambers.choices:
        if not origin_chamber:
            return None
        if origin_chamber == "Senado":
            return ProjectChambers.SENATORS
        return ProjectChambers.DEPUTIES

    @classmethod
    def clean_status(cls, status: str) -> ProjectStatus.choices:
        status_mapping = {
            "En comisiones, cámara de origen": ProjectStatus.ORIGIN_CHAMBER_COMISSION,
            "Con dictamen de comisiones, cámara de origen": ProjectStatus.ORIGIN_CHAMBER_SENTENCE,
            "Media sanción": ProjectStatus.HALF_SANCTION,
            "En comisiones, cámara revisora": ProjectStatus.REVISION_CHAMBER_COMISSION,
            "Con dictamen de comisiones, cámara revisora": ProjectStatus.REVISION_CHAMBER_SENTENCE,
        }
        return status_mapping.get(status, None)

    @classmethod
    def extract_project_info(cls, text):
        project_title = cls.get_project_tile(text)
        publication_date = cls.get_publication_date(text)
        origin_chamber = cls.get_origin_chamber(text)
        file_id = cls.get_file_id(text)
        status = cls.get_project_status(text)
        project_info = {
            "title": project_title,
            "publication_date": publication_date,
            "origin_chamber": origin_chamber,
            "status": status,
        }
        if origin_chamber == ProjectChambers.DEPUTIES:
            project_info["deputies_project_id"] = file_id
        else:
            project_info["senate_project_id"] = file_id
        if not origin_chamber:
            # Esto puede pasar por proyectos de Legislatura por ejemplo, no nos interesan
            return None
        return project_info

    @classmethod
    def get_data(cls, starting_page: int, step_size: int, projects_info=list) -> int:
        # gets data of 10
        ending_page = starting_page + step_size
        cls.logger.info(f"Retrieving data from page {starting_page} to {ending_page}...")
        projects_info = []
        total_added = 0
        for i in range(starting_page, ending_page):
            added = cls.retrieve_items(page=i, projects_info=projects_info)
            total_added += added
            if not added:
                break
        data = pd.DataFrame(projects_info)
        data["source"] = cls.__name__
        cls.logger.info(f"Retrieved {len(data)} projects")
        return data, total_added


class DeputyLawProjectsSource(DataSource):
    session = requests.Session()
    base_url = "https://www.diputados.gov.ar/proyectos/resultados-buscador.html"
    POST_HEADERS = {
        "Referer": "https://www.diputados.gov.ar/proyectos/index.html",
    }
    GET_HEADERS = {
        "Referer": "https://www.diputados.gov.ar/proyectos/resultados-buscador.html",
    }

    QUERY_DATA = {
        "strTipo": "ley",
        "strNumExp": "",
        "strNumExpOrig": "",
        "strNumExpAnio": "",
        "strCamIni": "",
        "strFechaInicio": "",
        "strFechaFin": "",
        "strMostrarTramites": "off",
        "strMostrarDictamenes": "off",
        "strMostrarFirmantes": "off",
        "strMostrarComisiones": "off",
        "strCantPagina": "100",
    }
    column_mappings = {
        "expediente diputados:": "deputies_project_id",
        "expediente senado:": "senate_project_id",
        "fecha:": "publication_date",
        "iniciado en:": "origin_chamber",
        "title": "title",
        "law": "law",
    }

    @classmethod
    def extract_project_info(cls, metadata) -> dict:
        spans = metadata.find_all("span")
        # Create an empty dictionary to store the data
        project_info = {}

        # Loop through the spans and extract the data
        for span in spans:
            key = span.find("strong").text.strip()
            if "LEY" in span.text:
                law_number = digitize_text(key)
                project_info["law"] = law_number
                continue
            value = span.contents[1].strip()
            project_info[key] = value
        return project_info

    @classmethod
    def send_request(cls, page_number):
        if page_number == 1:
            url = cls.base_url
            cls.logger.info(f"Sending POST request to {url}...")
            response = cls.session.post(url, data=cls.QUERY_DATA, headers=cls.POST_HEADERS)
        else:
            url = f"{cls.base_url}?pagina={page_number}"
            cls.logger.info(f"Sending GET request to {url}...")
            response = cls.session.get(url, headers=cls.GET_HEADERS)
        return response

    @classmethod
    def retrieve_items(cls, page, first_time: bool, projects_info: List[dict]) -> int:
        if first_time:
            response = cls.send_request(page_number=1)  # always, the POST request
        if page != 1:
            response = cls.send_request(page_number=page)
        page_content = response.content

        soup = BeautifulSoup(page_content, "html.parser")
        projects = soup.find_all(class_="detalle-proyecto")
        added = 0
        for project in projects:
            metadata = project.find(class_="dp-metadata")
            project_text = project.find(class_="dp-texto")
            project_info = cls.extract_project_info(metadata)
            project_info["title"] = project_text.get_text()
            project_info.pop("Publicado en:", None)
            projects_info.append(project_info)
            added += 1

        return added

    @classmethod
    def fix_date_format(cls, original_date: str) -> str:
        date = dt.datetime.strptime(original_date, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")

    @classmethod
    def get_data(cls, starting_page: int, first_time: bool, step_size: int, projects_info=list) -> int:
        ending_page = starting_page + step_size
        cls.logger.info(f"Retrieving data from page {starting_page}...")
        projects_info = []
        total_added = 0
        for i in range(starting_page, ending_page):
            added = cls.retrieve_items(page=i, first_time=first_time, projects_info=projects_info)
            total_added += added
            if not added:
                break
        data = pd.DataFrame(projects_info)
        data = cls.get_and_rename_relevant_columns(data)
        if "publication_date" not in data.columns:
            cls.logger.warning(f"No data retrieved from page {starting_page}, re-trying...")
            # especial, para marcar un problema con la request, reintentar
            return -1, -1
        data["publication_date"] = data["publication_date"].apply(cls.fix_date_format)
        data["source"] = "Diputados"
        cls.logger.info(f"Retrieved {len(data)} projects")
        return data, total_added
