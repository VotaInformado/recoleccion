import re
import datetime as dt
import time
from typing import List
import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from dateutil.parser import parse, ParserError

# Project
from recoleccion.components.utils import digitize_text
from recoleccion.components.data_sources import DataSource
from recoleccion.utils.custom_logger import CustomLogger
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
        cls.logger.info(f"Base LAW projects data size: {len(df.shape)}")
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
        return base_data.merge(
            extra_data, left_on="proyecto_id", right_on="expediente_id", how="left"
        )

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
                cls.logger.warning(
                    f"An error occurred at item {i} while extracting project info: {e}"
                )
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
        cls.logger.info(
            f"Retrieving data from page {starting_page} to {ending_page}..."
        )
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
            response = cls.session.post(
                url, data=cls.QUERY_DATA, headers=cls.POST_HEADERS
            )
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
    def get_data(
        cls, starting_page: int, first_time: bool, step_size: int, projects_info=list
    ) -> int:
        ending_page = starting_page + step_size
        cls.logger.info(f"Retrieving data from page {starting_page}...")
        projects_info = []
        total_added = 0
        for i in range(starting_page, ending_page):
            added = cls.retrieve_items(
                page=i, first_time=first_time, projects_info=projects_info
            )
            total_added += added
            if not added:
                break
        data = pd.DataFrame(projects_info)
        data = cls.get_and_rename_relevant_columns(data)
        if "publication_date" not in data.columns:
            cls.logger.warning(
                f"No data retrieved from page {starting_page}, re-trying..."
            )
            # especial, para marcar un problema con la request, reintentar
            return -1, -1
        data["publication_date"] = data["publication_date"].apply(cls.fix_date_format)
        data["source"] = "Diputados"
        cls.logger.info(f"Retrieved {len(data)} projects")
        return data, total_added


class SenateLawProjectsSource(DataSource):
    def __init__(self, threading=True):
        self.session = requests.Session()
        self.threading = threading
        self.logger = CustomLogger(threading=threading)
        self.deputies_exp = re.compile(self.DEPUTIES_PROJECT_ID_PATTERN)
        self.date_exp = re.compile(self.DATE_PATTERN)

    DEPUTIES_PROJECT_ID_PATTERN = r"(\d{1,4}-[A-Z,a-z]{1,3}-\d{1,4})"
    DATE_PATTERN = r"\b\d{2}-\d{2}-\d{4}\b"
    ROWS_PER_PAGE = 100
    BASE_URL = "https://www.senado.gob.ar/parlamentario/parlamentaria/avanzada"
    POST_HEADERS = {
        "Referer": "https://www.senado.gob.ar/parlamentario/parlamentaria/avanzada",
    }
    GET_HEADERS = {
        "Referer": "https://www.senado.gob.ar/parlamentario/parlamentaria/avanzada",
    }

    QUERY_DATA = {
        "busqueda_proyectos[autor]": "",
        "busqueda_proyectos[palabra]": "",
        "busqueda_proyectos[opcion]": "Y",
        "busqueda_proyectos[palabra2]": "",
        "busqueda_proyectos[comision]": "",
        "busqueda_proyectos[tipoDocumento]": "",
        "busqueda_proyectos[expedienteLugar]": "",
        "busqueda_proyectos[expedienteNumeroPre]": "",
        "busqueda_proyectos[expedienteNumeroPos]": "",
        "busqueda_proyectos[expedienteTipo]": "PL",
    }
    column_mappings = {
        "expediente diputados:": "deputies_project_id",
        "expediente senado:": "senate_project_id",
        "fecha:": "publication_date",
        "iniciado en:": "origin_chamber",
        "title": "title",
        "law": "law",
    }

    def get_payload(self, year: int):
        payload = self.QUERY_DATA.copy()
        payload["busqueda_proyectos[expedienteNumeroPos]"] = year
        return payload

    def get_origin_chamber(self, raw_chamber: str):
        chambers_info = {
            "S": ProjectChambers.SENATORS,
            "Senado De La Nación": ProjectChambers.SENATORS,
            "Poder Ejecutivo Nacional": ProjectChambers.SENATORS,
            "PE": ProjectChambers.SENATORS,
            "D": ProjectChambers.DEPUTIES,
            "CD": ProjectChambers.DEPUTIES,
            "Cámara De Diputados": ProjectChambers.DEPUTIES,
        }
        return chambers_info.get(raw_chamber, None)

    def get_project_info(self, project_id: str, source: str, title: str):
        origin_chamber = self.get_origin_chamber(source)
        if len(source) <= 3:
            project_number, project_year = project_id.split("/")
            project_id = f"{project_number}/{source}/{project_year}"
        project_info = {
            "senate_project_id": project_id,
            "origin_chamber": origin_chamber,
            "title": title,
        }
        return project_info

    def get_publication_date(self, page_content):
        raw_content = page_content.decode("utf-8")
        matches = self.date_exp.finditer(raw_content)
        if not matches:
            return None
        matched_dates = [match.group() for match in matches]
        dates = [self.fix_date_format(date) for date in matched_dates]
        # remove dates before the year 1800 (to remove bad matches)
        filtered_dates = [date for date in dates if int(date.split("-")[0]) >= 1800]
        min_date = min(filtered_dates)
        return min_date

    def get_deputies_project_id(self, page_content):
        soup = BeautifulSoup(page_content, "html.parser")
        project_id_element = soup.find("div", {"id": "etapaDiputado"})
        if not project_id_element:
            return None
        match = self.deputies_exp.findall(project_id_element.get_text())
        deputies_project_id = match[0] if match else None
        return deputies_project_id

    def get_details_of_project(self, link: str):
        url = f"https://www.senado.gob.ar{link}"
        response = self.session.get(url)
        content = response.content
        publication_date = self.get_publication_date(content)
        deputies_project_id = self.get_deputies_project_id(content)
        return publication_date, deputies_project_id

    def send_base_request(self, year: int):
        url = self.BASE_URL
        self.logger.info(f"Sending base POST request to {url}...")
        response = self.session.post(
            url, data=self.get_payload(year), headers=self.POST_HEADERS
        )
        return response

    def send_page_request(self, page_number):
        url = f"{self.BASE_URL}?cantRegistros={self.ROWS_PER_PAGE}&page={page_number}"
        self.logger.info(f"Sending GET request to {url}...")
        response = self.session.get(url, headers=self.GET_HEADERS)
        return response

    def get_page_info(self, page: int):
        page_info = []
        response = self.send_page_request(page)
        response_body = response.content
        soup = BeautifulSoup(response_body, "html.parser")
        table_data_element = soup.find("table", {"summary": "Listado de Proyectos"})
        if not table_data_element:
            return page_info  # no data
        table_rows = table_data_element.find_all("tr")
        for i, row in enumerate(table_rows[1:]):
            cells = row.find_all("td")
            cell_texts = [cell.text.strip() for cell in cells]
            project_id, project_type, source, title = cell_texts
            self.logger.info(f"Extracting info from project: {project_id}")
            try:
                link = cells[0].find("a")["href"]
                publication_date = None
                deputies_project_id = None
                if link:
                    source = link.split("/")[-2]
                    publication_date, deputies_project_id = self.get_details_of_project(
                        link
                    )

                project_info = self.get_project_info(project_id, source, title)
                project_info["publication_date"] = publication_date
                project_info["deputies_project_id"] = deputies_project_id
                page_info.append(project_info)
            except BaseException as e:
                self.logger.error(
                    f"An error occurred at project {i} while extracting project info: {e}"
                )
                continue
        return page_info

    def get_year_info(self, year: int):
        # Make the HTTP request
        year_info = []
        self.logger.info(f"Requesting info for year {year}...")
        self.send_base_request(year)
        page = 1
        while True:
            page_info = self.get_page_info(page)
            if not page_info:
                break
            year_info.extend(page_info)
            page += 1
        return year_info

    def fix_date_format(self, date: str):
        final_format = "%Y-%m-%d"
        try:
            return parse(date, dayfirst=True).strftime(final_format)
        except ParserError:
            initial_format = "%d-%m-%Y"
            return dt.datetime.strptime(date, initial_format).strftime(final_format)

    def get_data(self, year: int):
        projects_info = self.get_year_info(year)
        data = pd.DataFrame(projects_info)
        data["source"] = "Senadores (web)"
        self.logger.info(f"Retrieved {len(data)} projects")
        return data
