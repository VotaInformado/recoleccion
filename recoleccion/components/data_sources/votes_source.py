import io
import re
from typing import List, Tuple
import requests
import pandas as pd
from bs4 import BeautifulSoup
import PyPDF2
import datetime as dt


# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.components.utils import capitalize_text, trim_extra_spaces
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_types import VoteTypes


class DatasetVotesSource(DataSource):
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


class DeputyVotesSource(DataSource):
    BASE_URL = "https://votaciones.hcdn.gob.ar/votaciones/search"
    ALTERNATIVE_URL = "http://host.docker.internal:8001/scrape-page/"
    column_mappings = {
        "expediente": "project_id",
        "diputado_nombre": "diputado_nombre",  # igual después se divide en name y last_name
        "bloque": "party",
        "distrito_nombre": "province",
        "voto": "vote",
        "titulo": "reference_description",
    }

    @classmethod
    def get_legislator_name(cls, raw_name: str) -> Tuple[str, str]:
        last_name, name = raw_name.split(",", 1)
        name, last_name = trim_extra_spaces(name), trim_extra_spaces(last_name)
        name, last_name = capitalize_text(name), capitalize_text(last_name)
        return name, last_name

    @classmethod
    def get_project_info(cls, raw_info: str) -> dict:
        date_pattern = r"(\d{2}/\d{2}/\d{4})"
        # Find and extract publication date
        date_search = re.search(date_pattern, raw_info)
        date = date_search.group(1) if date_search else None

        # Use publication date as a reference to extract the project title
        project_title = re.split(date_pattern, raw_info)[0].strip()
        return {
            "reference_description": project_title,
            "date": date,
        }

    @classmethod
    def get_project_votes_info(cls, link: str) -> List[dict]:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            project_info_box = soup.find_all("div", class_="white-box")[0]
        except Exception as e:
            cls.logger.warning(f"Error while getting project info from {link}: {e}")
            return None
        project_info = cls.get_project_info(project_info_box.text.strip())
        table_data_element = soup.find(id="myTable")
        try:
            table_rows = table_data_element.find_all("tr")
        except Exception as e:
            cls.logger.warning(f"Error while getting project votes from {link}: {e}")
            return None
        project_votes_info = []
        for row in table_rows:
            row_data = row.find_all("td")
            if len(row_data) > 0:
                name, last_name = cls.get_legislator_name(row_data[1].text.strip())
                party = row_data[2].text.strip()
                province = row_data[3].text.strip()
                vote = row_data[4].text.strip()
                vote_info = {
                    "name": name,
                    "last_name": last_name,
                    "party": party,
                    "province": province,
                    "vote": vote,
                }
                project_votes_info.append(vote_info)
        for vote_info in project_votes_info:
            vote_info.update(project_info)
        return project_votes_info

    @classmethod
    def get_project_titles(cls, table_data_element):
        rows = table_data_element.find_all("tr")
        # Extract values from the second column of each row
        second_column_values = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                title = cells[1].text.strip()
                second_column_values.append(title)

    @classmethod
    def get_references_from_pdf(cls, pdf_link: str) -> str:
        response = requests.get(pdf_link)
        pdf_stream = io.BytesIO(response.content)
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
        except Exception as e:
            cls.logger.warning(f"Error while reading PDF from {pdf_link}: {e}")
            return None
        page_text = pdf_reader.pages[0].extract_text()
        project_id_pattern = r"\b\d{1,4}-[A-Z]-\d{2,4}\b"
        day_order_pattern = r"O.D. \d+"
        project_ids = re.findall(project_id_pattern, page_text)
        day_orders = re.findall(day_order_pattern, page_text)
        day_orders = [order.replace("O.D.", "").strip() for order in day_orders]
        reference_info = {
            "project_ids": project_ids,
            "day_orders": day_orders,
        }
        return reference_info

    @classmethod
    def build_projects_info(cls, project_info: List[dict], references_info: dict) -> List[List[dict]]:
        """
        Importante: una "única" votación puede estar asociada a varios proyectos (order_days o project_ids)
        Recibe info de un proyecto y de las referencias a ese proyecto.
        Devuelve tantos diccionarios como referencias haya, con la info del proyecto.
        Cada diccionario representa información sobre un voto.
        """
        project_ids = references_info["project_ids"]
        day_orders = references_info["day_orders"]
        projects_info = []
        if project_ids:
            for project_id in project_ids:
                project_info_copy = project_info.copy()
                for vote_info in project_info_copy:
                    vote_info["project_id"] = project_id
                projects_info.append(project_info_copy)
            return projects_info  # si hay project_ids, mejor que no recorra los day_orders
        else:
            for day_order in day_orders:
                try:
                    day_order = int(day_order)
                except ValueError:
                    continue
                project_info_copy = project_info.copy()
                for vote_info in project_info_copy:
                    vote_info["day_order"] = day_order
                projects_info.append(project_info_copy)
            return projects_info

    @classmethod
    def get_pdf_link(cls, row):
        base_link_url = "https://votaciones.hcdn.gob.ar"
        pdf_buttons = row.find_all("a", {"title": "Ver PDF"})
        if not pdf_buttons:
            pdf_buttons = row.find_all("a", {"title": "Ver PDF virtual"})
        if pdf_buttons:
            pdf_button = pdf_buttons[0]
            pdf_link = base_link_url + pdf_button["href"]
            return pdf_link
        pdf_buttons = row.find_all("button", {"title": "Ver PDF"})
        if not pdf_buttons:
            pdf_buttons = row.find_all("buttons", {"title": "Ver PDF virtual"})
        pdf_button = pdf_buttons[0]
        pdf_url_match = re.search(r"'(https://[^']+)'", pdf_button["onclick"])
        if pdf_url_match:
            return pdf_url_match.group().replace("'", "")
        return None

    @classmethod
    def get_rows_info(cls, table_data_element):
        table_rows = table_data_element.find_all("tr")
        base_link_url = "https://votaciones.hcdn.gob.ar"
        projects_ids, pdf_links, details_links = [], [], []
        for row in table_rows[1:]:
            project_id_pattern = re.compile(r"\b\d{1,4}-[A-Z]-\d{2,4}\b")
            detail_button = row.find("a", title="Ver detalle")
            detail_link = base_link_url + detail_button["href"]
            spans = row.find_all("span")
            project_ids = [span.get_text().strip() for span in spans if project_id_pattern.match(span.get_text())]
            projects_ids.append(project_ids)
            if project_ids:
                cls.logger.info(f"Found project IDs: {project_ids}")
            pdf_link = cls.get_pdf_link(row) if not project_ids else None
            if pdf_link:
                cls.logger.info(f"Found PDF link: {pdf_link}")
            pdf_links.append(pdf_link)
            details_links.append(detail_link)
        return projects_ids, pdf_links, details_links

    @classmethod
    def get_year_info(cls, year: int):
        # Make the HTTP request
        total_info = []
        last_retrieved_year = getattr(cls, "last_retrieved_year", None)
        if year == last_retrieved_year:
            cls.logger.info(f"Using cached info for year {year}...")
            response_body = cls.get_last_retrieved_body
        else:
            cls.logger.info(f"Requesting info for year {year}...")
            # response = requests.post(cls.BASE_URL, {"anoSearch": str(year)})
            body = {"year": str(year)}
            response = requests.post(cls.ALTERNATIVE_URL, body)
            response_body = response.json()["content"]
            cls.last_retrieved_year = year
            cls.get_last_retrieved_body = response_body
        # Check if the request was successful (status code 200)
        soup = BeautifulSoup(response_body, "html.parser")
        table_data_element = soup.find(id="table-data")
        projects_ids, pdf_links, details_links = cls.get_rows_info(table_data_element)
        all_links = zip(projects_ids, details_links, pdf_links)
        year_votes_info = []
        for project_ids, details_link, pdf_link in all_links:
            project_votes_info = cls.get_project_votes_info(details_link)
            if project_ids:
                references = {"project_ids": project_ids, "day_orders": []}
            else:
                references = cls.get_references_from_pdf(pdf_link)
            if not references or not project_votes_info:
                cls.logger.warning(f"Skipping project {project_ids}...")
                continue

            year_votes_info.extend(project_votes_info)
            projects_info = cls.build_projects_info(project_votes_info, references)
            for project_info in projects_info:
                total_info.extend(project_info)
        return total_info

    @classmethod
    def fix_date_format(cls, original_date: str) -> str:
        date = dt.datetime.strptime(original_date, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")

    @classmethod
    def get_data(cls, year: int):
        votes_info = cls.get_year_info(year=year)
        data = pd.DataFrame(votes_info)
        data["date"] = data["date"].apply(cls.fix_date_format)
        data["chamber"] = ProjectChambers.DEPUTIES
        data["source"] = "Diputados"
        cls.logger.info(f"Retrieved {len(data)} votes for year {year}")
        if "day_order" in data.columns:
            day_order_grouped = data.groupby("day_order")["vote"].count()
            assert (day_order_grouped % 257 == 0).all()
            print(f"Most common day_order: {max(day_order_grouped)}")
        if "project_id" in data.columns:
            project_id_grouped = data.groupby("project_id")["vote"].count()
            assert (project_id_grouped % 257 == 0).all()

        return data


class SenateVotesSource(DataSource):
    BASE_REQUEST_URL = "https://www.senado.gob.ar/votaciones/actas"
    YEAR_REQUEST_URL = "https://www.senado.gob.ar/votaciones/actas#"
    ALTERNATIVE_URL = "http://host.docker.internal:8001/scrape-page/"
    column_mappings = {
        "expediente": "project_id",
        "diputado_nombre": "diputado_nombre",  # igual después se divide en name y last_name
        "bloque": "party",
        "distrito_nombre": "province",
        "voto": "vote",
        "titulo": "reference_description",
    }
    session = requests.Session()

    @classmethod
    def make_base_request(cls):
        response = cls.session.get(cls.BASE_REQUEST_URL)
        if response.status_code != 200:
            raise Exception("Error while making base request")

    @classmethod
    def make_year_request(cls, year: int):
        data = {
            "busqueda_actas[anio]": str(year),
            "busqueda_actas[titulo]": "",
        }
        cls.logger.info(f"Requesting info for year {year}...")
        response = cls.session.post(cls.YEAR_REQUEST_URL, data=data)
        if response.status_code != 200:
            raise Exception(f"Error while making year request for year {year}")
        return response

    @classmethod
    def transform_string(cls, input_str):
        # Define regex patterns to extract components
        pattern = r"^([A-Z]+)-(\d+)/(\d+)-(\w+)$"
        match = re.match(pattern, input_str)

        # Rearrange components
        if match:
            prefix, num1, num2, suffix = match.groups()
            return f"{num1}-{prefix}-{num2}"
        else:
            cls.logger.warning(f"Could not transform string {input_str}")
            return input_str

    @classmethod
    def get_project_ids(cls, row: BeautifulSoup):
        project_div = row.find("div", class_="expedientesOcultos")
        if not project_div:
            return []
        links = project_div.find_all("a", href=lambda value: value and "verExp" in value)
        link_pattern = re.compile(r"[A-Z0-9]+-\S+")
        link_texts = [link.text.strip() for link in links]
        project_ids = [link for link in link_texts if link_pattern.match(link)]
        law_project_ids = [p_id for p_id in project_ids if p_id.endswith("PL")]
        law_project_ids = [cls.transform_string(p_id) for p_id in law_project_ids]
        project_ids_from_orders = cls.get_project_ids_from_orders(row)
        total_project_ids = law_project_ids + project_ids_from_orders
        total_project_ids = list(set(total_project_ids))  # remove duplicates
        return total_project_ids

    @classmethod
    def get_project_ids_from_day_order(cls, link: str):
        base_url = "https://www.senado.gob.ar"
        url = base_url + link
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:  # algunas ordenes no tienen expedientes asociados
            return []
        rows = table.find_all("tr")[1:]
        project_ids = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                raw_project_id = cells[1].text.strip()
                project_id_pattern = re.compile(r"[A-Z0-9]+-\S+")
                order_project_ids = project_id_pattern.findall(raw_project_id)
                project_ids.extend(order_project_ids)
        return project_ids

    @classmethod
    def get_project_ids_from_orders(cls, row: BeautifulSoup):
        project_div = row.find("div", class_="expedientesOcultos")
        if not project_div:
            return []
        links = project_div.find_all("a", href=lambda value: value and "orden" in value)
        od_pattern = re.compile(r"(?:O\.D\.|OD) \d+/\d+")
        link_texts = [link.text.strip() for link in links]
        day_orders = [links[i] for i, link in enumerate(link_texts) if od_pattern.match(link)]
        day_orders_links = [link["href"] for link in day_orders]
        project_ids = []
        for link in day_orders_links:
            order_project_ids = cls.get_project_ids_from_day_order(link)
            project_ids.extend(order_project_ids)
        project_ids = [cls.transform_string(p_id) for p_id in project_ids]
        return project_ids

    @classmethod
    def get_headers(cls, table):
        headers = {}
        top_row = table.find_all("tr")[0]
        top_row_cells = top_row.find_all("th")
        for i in range(len(top_row_cells)):
            header_name = top_row_cells[i].get_text()
            headers[header_name] = i
        return headers

    @classmethod
    def get_vote_info(cls, cells, headers, vote_date, vote_type):
        full_name = cells[headers["Senador"]].get_text()
        full_name = full_name.capitalize()
        last_name, name = full_name.split(",")
        name, last_name = trim_extra_spaces(name), trim_extra_spaces(last_name)
        name, last_name = capitalize_text(name), capitalize_text(last_name)
        party = cells[headers["Bloque"]].get_text()
        province = cells[headers["Provincia"]].get_text()
        try:
            vote = cells[headers["¿Cómo votó?"]].find("span").get_text()
        except Exception as e:
            return None
        info = {
            "name": name,
            "last_name": last_name,
            "party": party,
            "province": province,
            "vote": vote,
            "date": vote_date,
            "vote_type": vote_type,
        }
        return info

    @classmethod
    def get_votes_info(cls, details_link: str, vote_date: str, vote_type: str):
        votes_info = []
        base_url = "https://www.senado.gob.ar"
        url = base_url + details_link
        response = cls.session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        headers = cls.get_headers(table)
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            vote_info = cls.get_vote_info(cells, headers, vote_date, vote_type)
            if not vote_info:
                break  # algunas páginas no tienen los votos (https://www.senado.gob.ar/votaciones/detalleActa/749)
            votes_info.append(vote_info)
        return votes_info

    @classmethod
    def assemble_projects_info(cls, votes_info: List[dict], project_ids: List[str], project_law: str) -> List[dict]:
        projects_info = []
        for project_id in project_ids:
            for vote_info in votes_info:
                vote_info_copy = vote_info.copy()
                vote_info_copy["project_id"] = project_id
                projects_info.append(vote_info_copy)
        if project_law:
            for vote_info in votes_info:
                vote_info_copy = vote_info.copy()
                vote_info_copy["law"] = project_law
                projects_info.append(vote_info_copy)
        return projects_info

    @classmethod
    def get_project_law(cls, row: BeautifulSoup):
        cells = row.find_all("td")
        text = cells[2].get_text().strip()
        pattern = r"Ley \d{1,3}(?:\.\d{3})?"
        regex = re.compile(pattern, re.IGNORECASE)
        match = regex.search(text)
        if not match:
            return None
        raw_law = match.group()
        law = raw_law.replace("Ley ", "").replace("LEY ", "").replace(".", "").replace("'", "").strip()
        law = int(law)
        return law

    @classmethod
    def get_vote_date(cls, row: BeautifulSoup):
        cells = row.find_all("td")
        text = cells[0].get_text().strip()
        pattern = r"\d{2}/\d{2}/\d{4}"
        regex = re.compile(pattern, re.IGNORECASE)
        match = regex.search(text)
        if not match:
            return None
        return match.group()

    @classmethod
    def get_vote_type(cls, row: BeautifulSoup):
        cells = row.find_all("td")
        text = cells[3].get_text().strip()
        if "GENERAL" in text:
            return VoteTypes.GENERAL
        elif "PARTICULAR" in text:
            return VoteTypes.PARTICULAR
        return VoteTypes.OTHER

    @classmethod
    def get_year_info(cls, year: int):
        year_info = []
        cls.make_base_request()
        response = cls.make_year_request(year)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")
        # headers = get_headers(table)
        rows = table.find_all("tr")[1:]
        for row in rows:
            vote_date = cls.get_vote_date(row)
            vote_type = cls.get_vote_type(row)
            project_ids = cls.get_project_ids(row)
            if not project_ids:
                project_law = cls.get_project_law(row)
            else:
                project_law = None
            detail_element = row.find("a", title="Detalle")
            if not detail_element:  # algunas filas no tienen el botón de detalle de votación
                cls.logger.warning("No vote details link found, skipping...")
                continue
            vote_details_link = detail_element.get("href")
            if not project_ids and not project_law:
                cls.logger.warning(f"No projects nor law found, skipping row with link {vote_details_link}...")
                continue
            votes_info = cls.get_votes_info(vote_details_link, vote_date, vote_type)
            if not votes_info:
                cls.logger.warning(f"No votes found, skipping row with link {vote_details_link}...")
                continue
            projects_votes_info = cls.assemble_projects_info(votes_info, project_ids, project_law)
            year_info.extend(projects_votes_info)
        return year_info

    @classmethod
    def fix_date_format(cls, original_date: str) -> str:
        date = dt.datetime.strptime(original_date, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")

    @classmethod
    def get_data(cls, year: int):
        votes_info = cls.get_year_info(year=year)
        data = pd.DataFrame(votes_info)
        data["date"] = data["date"].apply(cls.fix_date_format)
        data["chamber"] = ProjectChambers.SENATORS
        data["source"] = "Senado"
        return data
