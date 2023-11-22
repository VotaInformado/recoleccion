import datetime as dt
from typing import List
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Project
from recoleccion.components.data_sources import DataSource
from recoleccion.exceptions.custom import PageNotFound


class DeputiesDayOrderSource(DataSource):
    session = requests.Session()
    BASE_URL = "https://www2.hcdn.gob.ar/secparl/dcomisiones/s_od/buscador.html"

    @classmethod
    def retrieve_projects(cls, day_order: int, projects_div) -> List[dict]:
        projects = []
        for i in range(0, len(projects_div), 2):
            project_id = projects_div[i].text.strip()
            info = {
                "day_order": day_order,
                "project_id": project_id,
            }
            projects.append(info)
        return projects

    @classmethod
    def get_day_orders_data(cls, period: int) -> List[dict]:
        data = []
        url = f"{cls.BASE_URL}?periodo={period}"
        response = cls.session.get(url)
        if response.status_code == 500:
            raise PageNotFound()
        page_content = response.content

        soup = BeautifulSoup(page_content, "html.parser")
        table_element = soup.find("table", id="licitaciones")
        # TODO: filtrar sólo proyectos de ley
        rows = table_element.find_all("tr")[1:]  # Skip the header row
        rows = list(filter(lambda row: len(row) > 5, rows))  # Forros que son con su tabla mal hecha
        for row in rows:
            try:
                day_order = int(row.find_all("td")[1].text.strip())
            except ValueError:  # casos raros, como 442bis
                continue
            special_div = row.find_all("td")[5]
            projects_div = special_div.find_all("td")
            linked_projects: List[dict] = cls.retrieve_projects(day_order, projects_div)
            data.extend(linked_projects)

        return data

    @classmethod
    def fix_date_format(cls, original_date: str) -> str:
        date = dt.datetime.strptime(original_date, "%d/%m/%Y")
        return date.strftime("%Y-%m-%d")

    @classmethod
    def get_data(cls, period: int) -> int:
        cls.logger.info(f"Retrieving data from period {period}...")
        data = cls.get_day_orders_data(period=period)
        data = pd.DataFrame(data)
        return data
