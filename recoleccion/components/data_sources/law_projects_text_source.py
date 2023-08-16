from recoleccion.components.data_sources import DataSource
from bs4 import BeautifulSoup
import requests
from recoleccion.utils.pdf_reader import Pdf
from recoleccion.components.utils import len_gt
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
    def get_text(cls, number, source, year):
        cls.logger.info(f"Getting text for project: {number}-{source}-{year}")
        cls.QUERY_DATA["strNumExp"] = number
        cls.QUERY_DATA["strNumExpOrig"] = source
        cls.QUERY_DATA["strNumExpAnio"] = year

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
        if text is None or not len_gt(text, 10):
            infobase_link = cls._get_infobase_url(number, source, year)
            infobase_text = cls._get_text_from_infobase(infobase_link)
            if infobase_text and len_gt(infobase_text, 10):
                text = infobase_text
                link = infobase_link
        return text, link


class SenateLawProyectsText(DataSource):
    session = requests.Session()
    domain = "https://www.senado.gob.ar"
    base_url = "https://www.senado.gob.ar/parlamentario/comisiones/verExp/{number}.{year}/{source}/PL"

    @classmethod
    def _get_pdf_text(cls, url):  # TODO: remove duplicate
        cls.logger.info(f"Getting text from pdf: {url}")
        response = cls.session.get(url, stream=True)
        stream = BytesIO(response.content)
        pdf = Pdf(stream)
        return pdf.get_text_and_close()

    @classmethod
    def _get_final_text(cls, soup):
        final_text_container = soup.find("div", {"id": "textoDefinitivo"})
        link = final_text_container.find("a")
        if link and link["href"]:
            return cls._get_pdf_text(link["href"])
        else:
            return final_text_container.get_text("\n", strip=True)

    @classmethod
    def _get_final_text_link(cls, soup):
        final_text_container = soup.find("div", {"id": "textoDefinitivo"})
        link = final_text_container.find("a")
        if link and link["href"]:
            return link["href"]
        return None

    @classmethod
    def _get_initial_text(cls, page):
        initial_text_container = page.find("div", {"id": "textoOriginal"})
        link = initial_text_container.find("a")
        if link and link["href"]:
            link = (
                link["href"]
                if link["href"].startswith("http")
                else cls.domain + link["href"]
            )
            return cls._get_pdf_text(link)
        else:
            return initial_text_container.get_text("\n", strip=True)

    @classmethod
    def _get_initial_text_link(cls, page):
        initial_text_container = page.find("div", {"id": "textoOriginal"})
        link = initial_text_container.find("a")
        if link:
            return (
                link["href"]
                if link["href"].startswith("http")
                else cls.domain + link["href"]
            )
        else:
            return None

    @classmethod
    def get_text(cls, number, source, year):
        cls.logger.info(f"Getting text for project: {number}-{source}-{year}")
        number = str(int(number))  # remove leading zeros
        source = source.upper()
        year = year[-2:] if len(year) > 2 else year
        url = cls.base_url.format(number=number, source=source, year=year)
        response = cls.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text = cls._get_final_text(soup)
        link = url or cls._get_final_text_link(soup)
        if text is None or not len_gt(text, 20):
            initial_text = cls._get_initial_text(soup)
            if initial_text and len_gt(initial_text, 10):
                text = initial_text
                link = cls._get_initial_text_link(soup)
        return text, link
