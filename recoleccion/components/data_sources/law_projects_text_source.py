from recoleccion.components.data_sources import DataSource
from bs4 import BeautifulSoup
import requests
from recoleccion.utils.pdf_reader import Pdf
from io import BytesIO
import re


class DeputiesLawProyectsText(DataSource):
    session = requests.Session()
    base_url = "https://www.diputados.gov.ar/proyectos/resultados-buscador.html"
    infobase_url = "https://www.hcdn.gob.ar/folio-cgi-bin/om_isapi.dll?infobase=tp.nfo&softpage=Doc_Frame_Pg42&record=dochitfirst&advquery={exp}"
    infobase_record_url = "https://www.hcdn.gob.ar/folio-cgi-bin/om_isapi.dll?infobase=tp.nfo&record={record}&softpage=Document42"
    POST_HEADERS = {
        "Referer": "https://www.diputados.gov.ar/proyectos/index.html",
    }
    GET_HEADERS = {
        "Referer": "https://www.diputados.gov.ar/proyectos/resultados-buscador.html",
    }

    QUERY_DATA = {
        "strTipo": "todos",
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

    @classmethod
    def _get_pdf_text(cls, url):
        cls.logger.info(f"Getting text from pdf: {url}")
        response = cls.session.get(url, stream=True)
        stream = BytesIO(response.content)
        pdf = Pdf(stream)
        return pdf.get_text_and_close()

    @classmethod
    def _get_infobase_url(cls, number, source, year):
        year = year[-2:] if len(year) > 2 else year
        exp = f"{number}-{source}-{year}"
        return cls.infobase_url.format(exp=exp)

    @classmethod
    def _get_text_from_infobase(cls, url):
        response = cls.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        record_url = soup.find("frame").get("src", "")
        pattern = r"record=({[^}]+})"
        match = re.search(pattern, record_url)
        if not match:
            return ""
        record_name = match.group(1)
        cls.logger.info(f"Record ID found: {record_name}. Getting text...")
        response = cls.session.get(cls.infobase_record_url.format(record=record_name))
        soup = BeautifulSoup(response.content, "html5lib")
        record = soup.find("a", attrs={"name": record_name})
        # remove scripts
        scripts = record.find_all("script")
        for script in scripts:
            script.decompose()
        return record.get_text("\n", strip=True)

    @classmethod
    def _get_html_text(cls, url):
        cls.logger.info(f"Getting text from html: {url}")
        response = cls.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text_container = soup.find("div", attrs={"class": "container interno"})
        if not text_container:
            text_container = soup.find("div", attrs={"id": "proyectosTexto"})
        text = text_container.get_text("\n", strip=True)
        return text

    @classmethod
    def len_gt(cls, text, length):
        try:
            text[length]
            return True
        except IndexError:
            return False

    @classmethod
    def get_text(cls, number, source, year):
        cls.logger.info(f"Getting text for project: {number}-{source}-{year}")
        cls.QUERY_DATA["strNumExp"] = "3087"
        cls.QUERY_DATA["strNumExpOrig"] = "D"
        cls.QUERY_DATA["strNumExpAnio"] = "2023"

        response = cls.session.post(
            cls.base_url, data=cls.QUERY_DATA, headers=cls.POST_HEADERS
        )
        soup = BeautifulSoup(response.content, "html.parser")
        link_to_text = soup.find(
            "a", string=["Texto completo del proyecto", "Ver documento original"]
        )
        text = ""
        link = ""
        if link_to_text and link_to_text.get("href", "").endswith(".pdf"):
            link = link_to_text["href"]
            text = cls._get_pdf_text(link)
        elif link_to_text:
            link = link_to_text["href"]
            text = cls._get_html_text(link)
        if text is None or not cls.len_gt(text, 10):
            link = cls._get_infobase_url(number, source, year)
            text = cls._get_text_from_infobase(link)
        return text, link
