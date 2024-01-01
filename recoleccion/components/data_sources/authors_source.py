import re
import datetime as dt
from typing import List
import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging

# Project
from recoleccion.components.utils import (
    capitalize_text,
    digitize_text,
    trim_extra_spaces,
)
from recoleccion.components.data_sources import DataSource
from recoleccion.models.law_project import LawProject
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.project_status import ProjectStatus


logger = logging.getLogger(__name__)


class DeputiesAuthorsSource(DataSource):
    session = requests.Session()
    BASE_URL = "https://www.hcdn.gob.ar/proyectos/resultado.html"
    POST_HEADERS = {
        "Referer": "https://www.diputados.gov.ar/proyectos/index.html",
    }
    GET_HEADERS = {
        "Referer": "https://www.hcdn.gob.ar/proyectos/resultado.html",
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
        "strMostrarFirmantes": "on",
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

    PAGE_PATTERN = re.compile(r"Página \d{1,6} de (\d{1,6})")

    @classmethod
    def get_total_pages(cls):
        response = cls().send_base_request()
        content = response.content.decode("utf-8")
        match = cls.PAGE_PATTERN.search(content)
        if not match:
            return 0
        total_pages = int(match.group(1))
        return total_pages

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

    def send_page_request(self, page_number: int):
        url = f"{self.BASE_URL}?pagina={page_number}"
        self.logger.info(f"Sending GET request to {url}...")
        response = self.session.get(url, headers=self.GET_HEADERS)
        return response

    def send_base_request(self):
        url = self.BASE_URL
        logger.info(f"Sending POST request to {url}...")
        response = self.session.post(url, data=self.QUERY_DATA, headers=self.POST_HEADERS)
        return response

    def get_project_id_info(self, metadata) -> dict:
        spans = metadata.find_all("span")
        project_id_info = {}
        for span in spans:
            key = span.find("strong").text.strip()
            if "diputados" in key.lower():
                project_id_info["deputies_project_id"] = span.contents[1].strip()
            elif "senado" in key.lower():
                project_id_info["senate_project_id"] = span.contents[1].strip()
        return project_id_info

    def get_author_type(self, project_id_info: dict) -> str:
        if project_id_info.get("deputies_project_id", None):
            project_id = project_id_info["deputies_project_id"]
            origin_chamber = LawProject.get_project_origin_chamber(project_id)
        elif project_id_info.get("senate_project_id", None):
            project_id = project_id_info["senate_project_id"]
            origin_chamber = LawProject.get_project_origin_chamber(project_id)
        else:
            return None
        if origin_chamber == ProjectChambers.DEPUTIES:
            return LegislatorSeats.DEPUTY
        elif origin_chamber == ProjectChambers.SENATORS:
            return LegislatorSeats.SENATOR
        return None

    def retrieve_items(self, page: int) -> int:
        self.send_base_request()
        response = self.send_page_request(page_number=page)
        page_content = response.content

        page_info = []
        soup = BeautifulSoup(page_content, "html.parser")
        # projects = soup.find_all(class_="detalle-proyecto")
        projects_metadata = soup.find_all(class_="dp-metadata")
        projects_detail = soup.find_all(class_="detalle-proyecto")
        projects = zip(projects_metadata, projects_detail)

        for project_metada, project_detail in projects:
            project_id_info: dict = self.get_project_id_info(project_metada)
            if not project_id_info:
                logger.info(
                    "No deputies_project_id or senate_project_id info found, skipping..."
                )
                continue
            signers_table = project_detail.find('table', class_='table-striped')
            table_rows = signers_table.find_all("tr")
            author_type = self.get_author_type(project_id_info)
            project_id_info["author_type"] = author_type

            for row in table_rows[1:]:
                cells = row.find_all("td")
                if not cells:
                    logger.info("No signers info found, skipping...")
                signers_info = {
                    "raw_name": cells[0].text.strip(),
                    "party_name": cells[2].text.strip(),
                    "author_type": LegislatorSeats.DEPUTY,
                }
                signers_info.update(project_id_info)
                page_info.append(signers_info)
        return page_info

    def fix_date_format(self, original_date: str) -> str:
        date = dt.datetime.strptime(original_date, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")

    def clean_name(self, name: str) -> str:
        if not name:
            return name
        name = capitalize_text(name)
        name = trim_extra_spaces(name)
        return name

    def get_data(self, page: int):
        projects_info = self.retrieve_items(page)
        page_data = pd.DataFrame(projects_info)
        if page_data.empty:
            return page_data
        page_data[["last_name", "name"]] = page_data["raw_name"].str.split(
            ",", expand=True
        )
        page_data = page_data.drop(columns=["raw_name"])
        page_data = page_data.dropna(subset=["name", "last_name"])
        page_data = page_data.reset_index(drop=True)
        page_data["name"] = page_data["name"].apply(self.clean_name)
        page_data["last_name"] = page_data["last_name"].apply(self.clean_name)
        page_data["source"] = f"diputados_{page}"
        return page_data


class SenateAuthorsSource(DataSource):
    def __init__(self, threading=True):
        self.session = requests.Session()
        self.threading = threading
        self.logger = logging.getLogger(__name__)

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
            "D": ProjectChambers.DEPUTIES,
            "CD": ProjectChambers.DEPUTIES,
        }
        return chambers_info.get(raw_chamber, None)

    def get_project_info(self, project_id: str, origin_chamber: str, title: str):
        origin_chamber = self.get_origin_chamber(origin_chamber)
        project_info = {
            "senate_project_id": project_id,
        }
        return project_info

    def get_publication_date(self, raw_link: str):
        link = raw_link.find("a")["href"]
        url = f"https://www.senado.gob.ar{link}"
        response = self.session.get(url)
        raw_content = response.content.decode("utf-8")
        date_pattern = r"\b\d{2}-\d{2}-\d{4}\b"
        matches = re.finditer(date_pattern, raw_content)
        if not matches:
            return None
        matched_dates = [match.group() for match in matches]
        dates = [self.fix_date_format(date) for date in matched_dates]
        min_date = min(dates)
        return min_date

    def get_authors(self, raw_link: str) -> List[dict]:
        link = raw_link.find("a")["href"]
        url = f"https://www.senado.gob.ar{link}"
        response = self.session.get(url)
        raw_content = response.content.decode("utf-8")
        soup = BeautifulSoup(raw_content, "html.parser")
        authors = []
        authors_table = soup.find("table", {"summary": "Listado de Autores"})
        if not authors_table:
            return authors
        authors_rows = authors_table.find_all("tr")
        for row in authors_rows:
            author_cell = row.find("td")
            author_name = author_cell.text.strip()
            last_name, name = author_name.split(",")
            name, last_name = capitalize_text(name), capitalize_text(last_name)
            name, last_name = trim_extra_spaces(name), trim_extra_spaces(last_name)
            author_info = {"name": name, "last_name": last_name}
            authors.append(author_info)
        return authors

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

    def get_author_type(self, raw_origin_chamber: str):
        origin_chamber = self.get_origin_chamber(raw_origin_chamber)
        if origin_chamber == ProjectChambers.DEPUTIES:
            return LegislatorSeats.DEPUTY
        elif origin_chamber == ProjectChambers.SENATORS:
            return LegislatorSeats.SENATOR
        return None

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
            project_id, project_type, origin_chamber, title = cell_texts
            self.logger.info(f"Extracting info from project: {project_id}")
            authors_info: List[dict] = self.get_authors(cells[0])
            project_info = self.get_project_info(project_id, origin_chamber, title)
            author_type = self.get_author_type(origin_chamber)
            project_info["author_type"] = author_type
            for author_info in authors_info:
                author_info.update(project_info)
                page_info.append(author_info)
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
        initial_format = "%d-%m-%Y"
        final_format = "%Y-%m-%d"
        return dt.datetime.strptime(date, initial_format).strftime(final_format)

    def get_data(self, year: int):
        projects_info = self.get_year_info(year)
        data = pd.DataFrame(projects_info)
        data["source"] = f"senado_{year}"
        self.logger.info(f"Retrieved {len(data)} projects")
        return data
