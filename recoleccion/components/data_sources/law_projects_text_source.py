from recoleccion.components.data_sources import DataSource
from bs4 import BeautifulSoup
import requests
from recoleccion.utils.pdf_reader import Pdf
from recoleccion.components.utils import len_gt
from io import BytesIO
import re
from urllib3.util import Retry
from multiprocessing import current_process


class LawProjectsText(DataSource):
    # Base class for law projects text sources
    # This class is not meant to be used directly
    # Contains common methods used for both deputies and senators law projects text sources

    @classmethod
    def _get_pdf_text(cls, url):
        cls.logger.info(f"{current_process().name} > Getting text from pdf: {url}")
        try:
            response = cls.session.get(url, stream=True)
            if response.status_code != 200:
                cls.logger.error(
                    f"{current_process().name} > Error while getting pdf from url {url}: {response.status_code}"
                )
                return ""
            stream = BytesIO(response.content)
            pdf = Pdf(stream)
        except Exception as e:
            cls.logger.error(
                f"{current_process().name} > Error while getting pdf from url {url}: {e}",
                exc_info=True,
            )
            return ""
        return pdf.get_text_and_close()

    @classmethod
    def get_text(cls, number, source, year):
        from multiprocessing import current_process

        this_process = current_process().name
        cls.logger.info(
            f"{this_process} > Getting text for project: {number}-{source}-{year}"
        )
        text, link = cls._get_text(number, source, year)
        cls.logger.info(
            f"{this_process} > GOT text for project: {number}-{source}-{year}"
        )
        return text, link

    @classmethod
    def _get_text(cls, number, source, year):
        raise NotImplementedError


class DeputiesLawProjectsText(LawProjectsText):
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=None,  # To allow all
    )
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))
    base_url = "https://www.hcdn.gob.ar/proyectos/resultado.html"
    infobase_url = "https://www.hcdn.gob.ar/folio-cgi-bin/om_isapi.dll?infobase=tp.nfo&softpage=Doc_Frame_Pg42&record=dochitfirst&advquery={exp}"
    infobase_record_url = "https://www.hcdn.gob.ar/folio-cgi-bin/om_isapi.dll?infobase=tp.nfo&record={record}&softpage=Document42"
    POST_HEADERS = {
        "Referer": "https://www.hcdn.gob.ar/proyectos/",
    }
    GET_HEADERS = {
        "Referer": "https://www.hcdn.gob.ar/proyectos/resultado.html",
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
    def _get_infobase_url(cls, number, source, year):
        year = str(int(year))  # remove leading zeros
        year = year[-2:] if len(year) > 2 else year
        exp = f"{number}-{source}-{year}"
        return cls.infobase_url.format(exp=exp)

    @classmethod
    def _get_text_from_infobase(cls, url):
        response = cls.session.get(url)
        if response.status_code != 200:
            cls.logger.error(
                f"{current_process().name} > Error while getting infobase url: {url}: {response.status_code}"
            )
            return ""
        soup = BeautifulSoup(response.content, "html.parser")
        record_url = soup.find("frame").get("src", "") if soup.find("frame") else ""
        pattern = r"record=({[^}]+})"
        match = re.search(pattern, record_url)
        if not match:
            return ""
        record_name = match.group(1)
        infobase_url = cls.infobase_record_url.format(record=record_name)
        response = cls.session.get(infobase_url)
        if response.status_code != 200:
            cls.logger.error(
                f"{current_process().name} > Error while getting infobase record: {record_name} from url {infobase_url}: {response.status_code}"
            )
            return ""
        soup = BeautifulSoup(response.content, "html5lib")
        record = soup.find("a", attrs={"name": record_name})
        if not record:
            cls.logger.warning(
                f"{current_process().name} > Could not find record {record_name} in infobase url: {infobase_url}"
            )
            return ""
        # remove scripts
        scripts = record.find_all("script")
        for script in scripts:
            script.decompose()
        return record.get_text("\n", strip=True)

    @classmethod
    def _get_html_text(cls, url):
        response = cls.session.get(url)
        if response.status_code != 200:
            cls.logger.error(
                f"{current_process().name} > Error while getting html text from url: {url}: {response.status_code}"
            )
            return ""
        soup = BeautifulSoup(response.content, "html.parser")
        text_container = soup.find("div", attrs={"class": "container interno"})
        if not text_container:
            text_container = soup.find("div", attrs={"id": "proyectosTexto"})
        text = text_container.get_text("\n", strip=True)
        return text

    @classmethod
    def _get_text(cls, number, source, year):
        if not number or not source or not year:
            cls.logger.info(
                f"{current_process().name} > Missing data for project: {number}-{source}-{year}. Skipping..."
            )
            return "", None
        cls.QUERY_DATA["strNumExp"] = number
        cls.QUERY_DATA["strNumExpOrig"] = source
        cls.QUERY_DATA["strNumExpAnio"] = year

        response = cls.session.post(
            cls.base_url, data=cls.QUERY_DATA, headers=cls.POST_HEADERS
        )
        if response.status_code != 200:
            cls.logger.error(
                f"{current_process().name} > Error while getting projects from url {cls.base_url} for project {number}-{source}-{year}: {response.status_code}"
            )
            return "", None
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


class SenateLawProjectsText(LawProjectsText):
    session = requests.Session()
    domain = "https://www.senado.gob.ar"
    base_url = "https://www.senado.gob.ar/parlamentario/comisiones/verExp/{number}.{year}/{source}/PL"

    @classmethod
    def full_path(cls, path):
        return path if path.startswith("http") else cls.domain + path

    @classmethod
    def _get_final_text(cls, soup):
        final_text_container = soup.find("div", {"id": "textoDefinitivo"})
        if not final_text_container:
            return ""
        link = final_text_container.find("a")
        if link and link["href"]:
            link = cls.full_path(link["href"])
            return cls._get_pdf_text(link)
        else:
            return final_text_container.get_text("\n", strip=True)

    @classmethod
    def _get_final_text_link(cls, soup):
        final_text_container = soup.find("div", {"id": "textoDefinitivo"})
        link = final_text_container.find("a")
        if link and link["href"]:
            return cls.full_path(link["href"])
        return None

    @classmethod
    def _get_initial_text(cls, page):
        initial_text_container = page.find("div", {"id": "textoOriginal"})
        if not initial_text_container:
            return ""
        link = initial_text_container.find("a")
        if link and link["href"]:
            link = cls.full_path(link["href"])
            return cls._get_pdf_text(link)
        else:
            return initial_text_container.get_text("\n", strip=True)

    @classmethod
    def _get_initial_text_link(cls, page):
        initial_text_container = page.find("div", {"id": "textoOriginal"})
        link = initial_text_container.find("a")
        if link:
            return cls.full_path(link["href"])
        else:
            return None

    @classmethod
    def _parse_input(cls, number, source, year):
        number = str(int(number))  # remove leading zeros
        source = source.upper()
        year = str(int(year))  # remove leading zeros
        year = year[-2:] if len(year) > 2 else year
        return number, source, year

    @classmethod
    def _get_text(cls, number, source, year):
        if not number or not source or not year:
            cls.logger.info(
                f"{current_process().name} > Missing data for project: {number}-{source}-{year}. Skipping..."
            )
            return "", None
        number, source, year = cls._parse_input(number, source, year)
        url = cls.base_url.format(number=number, source=source, year=year)
        response = cls.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text = cls._get_final_text(soup)
        link = url or cls._get_final_text_link(soup)
        if text is None or not len_gt(text, 20):
            initial_text = cls._get_initial_text(soup)
            if initial_text and len_gt(initial_text, 10):
                text = initial_text
                link = cls._get_initial_text_link(soup) or link
        return text, link
