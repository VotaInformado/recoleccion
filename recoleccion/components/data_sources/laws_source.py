import io
from bs4 import BeautifulSoup
import requests
import pandas as pd
import logging

# Project
from recoleccion.components.data_sources import DataSource

logger = logging.getLogger(__name__)


class LawSource(DataSource):
    column_mappings = {
        "ley": "law_number",
        "titulo": "title",
        "sumario": "summary",
        "referencias": "tags",
        "fecha_publicacion": "publication_date",
        "decreto_promulgacion": "associated_decree",
        "veto": "veto",
        "expediente_inicial": "initial_file",
        "proyecto_id": "project_id",
    }

    @classmethod
    def get_publication_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=cbf78f72-1098-4e84-99e7-695d6d65a02a&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    @classmethod
    def get_laws_data(cls):
        url = "https://datos.hcdn.gob.ar:443/api/3/action/datastore_search?resource_id=3dc4e8e1-2148-4bf0-b9c9-f19cafc6ff8e&limit=10000"
        response = requests.get(url)
        data = response.json()["result"]["records"]
        return pd.DataFrame(data)

    @classmethod
    def get_sanction_data(cls):
        url = "https://datos.hcdn.gob.ar/dataset/5b1d2f38-e23f-412c-a286-02ab9dcf6082/resource/68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98/download/leyes_sancionadas1.5.csv"
        response = requests.get(url)
        data = response.content
        df = pd.read_csv(io.StringIO(data.decode("utf-8")))
        reduced_df = df[["ley", "expediente_inicial", "proyecto-id"]]
        return pd.DataFrame(reduced_df)

    @classmethod
    def extract_dates_from_datetimes(cls, datetime_str):
        key_index = datetime_str.find("T")
        return datetime_str[:key_index]

    @classmethod
    def get_data(cls):
        laws_data = cls.get_laws_data()
        cls.logger.info(f"Base laws data size: {len(laws_data)}")
        publication_data = cls.get_publication_data()
        cls.logger.info(f"Publication data size: {len(publication_data)}")
        data = laws_data.merge(publication_data, on="ley", how="left")
        cls.logger.info(f"First merge data size: {len(data)}")
        sanction_data = cls.get_sanction_data()
        cls.logger.info(f"Sanction data size: {len(sanction_data)}")
        data = data.merge(sanction_data, on="ley", how="left")
        cls.logger.info(f"Second merge data size: {len(data)}")
        data = cls.get_and_rename_relevant_columns(data)
        data["publication_date"] = data["publication_date"].map(cls.extract_dates_from_datetimes)
        return data


class GovernmentLawSource(DataSource):
    session = requests.Session()
    BASE_URL = (
        "https://www.argentina.gob.ar/normativa/buscar?jurisdiccion=nacional&tipo_norma=leyes&limit=50&offset={offset}"
    )
    DETAIL_URL_HEAD = "https://www.argentina.gob.ar"

    @classmethod
    def get(cls, url: str):
        logger.info(f"Making request to {url}")
        response = cls.session.get(url)
        return response

    @classmethod
    def _make_page_request(cls, page: int) -> requests.Response:
        url = cls.BASE_URL.format(offset=page)
        response = cls.get(url)
        return response

    @classmethod
    def _translate_date(cls, raw_date: str):
        MONTH_TRANSLATIONS = {
            "Ene": 1,
            "Feb": 2,
            "Mar": 3,
            "Abr": 4,
            "May": 5,
            "Mayo": 5,
            "Jun": 6,
            "Jul": 7,
            "Ago": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dic": 12,
        }
        day = raw_date[:2]
        year = raw_date[-4:]
        raw_month = raw_date[3:-5]
        month = MONTH_TRANSLATIONS[raw_month]
        return f"{year}-{month}-{day}"

    @classmethod
    def _get_law_number_and_link(cls, row):
        import re

        link = row.find("a")
        link_text = link.text.strip()
        link_url = link["href"]
        law_number = re.sub(r"\D", "", link_text)
        law_number = int(law_number)
        return law_number, link_url

    @classmethod
    def _get_publication_date(cls, row):
        try:
            date_element = row.find("td", {"class": "fecha"})
            link = date_element.find("a")  # Por qué es un link? No tiene sentido
            raw_date = link.text.strip()
            date = cls._translate_date(raw_date)
            return date
        except Exception:
            logger.warning("Unable to retrieve publication date")
            return None

    @classmethod
    def get_law_details_content(cls, law_link: str) -> BeautifulSoup:
        url = cls.DETAIL_URL_HEAD + law_link
        response = cls.get(url)
        data = response.content
        soup = BeautifulSoup(data, "html.parser")
        return soup

    @classmethod
    def _get_law_text(cls, law_link: str):
        soup = cls.get_law_details_content(law_link)
        try:
            button = soup.find("a", text="Texto completo de la norma")
            button_link = button["href"]
        except Exception as e:
            logger.warning(f"Unable to retrieve button link for law {law_link}")
            logger.info(f"Attemping to retrieve text from {law_link}/texto")
            button_link = f"{law_link}/texto"
        url = cls.DETAIL_URL_HEAD + button_link
        response = cls.get(url)
        data = response.content
        soup = BeautifulSoup(data, "html.parser")
        article = soup.find("article")
        law_text = article.text.strip()
        return law_text

    @classmethod
    def _get_law_summary(cls, law_link: str):
        try:
            soup = cls.get_law_details_content(law_link)
            summary_element = soup.find("div", {"class": "m-y-4"})
            summary_paragraphs = summary_element.find_all("p")
            summary = "\n".join([p.text.strip() for p in summary_paragraphs])
            return summary
        except Exception:
            logger.warning(f"Unable to retrieve summary for law {law_link}")
            return None

    @classmethod
    def _get_law_title(cls, row):
        description_element = row.find("td", {"class": "descripcion"})
        desc_element = description_element.find("h3")
        desc_text = desc_element.text.strip()
        label_element = description_element.find("div", {"class": "label label-default"})
        label_text = label_element.text.strip() if label_element else ""
        title = label_text if len(label_text) > len(desc_text) else desc_text
        return title

    @classmethod
    def get_page_data(cls, page: int, titles_only):
        page_data = []
        response = cls._make_page_request(page)
        data = response.content
        soup = BeautifulSoup(data, "html.parser")
        rows = soup.find_all("tr", {"class": "panel"})
        for i, row in enumerate(rows):
            law_number, law_link = cls._get_law_number_and_link(row)
            if not law_number:
                logger.warning("Unable to retrieve law's number skipping...")
            if not law_link:
                logger.warning(f"Unable to retrieve link for law {law_number}, skipping...")
            law_title = cls._get_law_title(row)
            if titles_only:
                law_info = {"law_number": law_number, "title": law_title}
                page_data.append(law_info)
                continue
            publication_date = cls._get_publication_date(row)
            law_summary = cls._get_law_summary(law_link)
            law_text = cls._get_law_text(law_link)
            law_info = {
                "law_number": law_number,
                "publication_date": publication_date,
                "text": law_text,
                "summary": law_summary,
                "title": law_title,
            }
            page_data.append(law_info)
        return pd.DataFrame(page_data)
