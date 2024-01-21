import requests
import pandas as pd
from typing import List
from bs4 import BeautifulSoup

# Project
from recoleccion.components.data_sources import DataSource


class LegislatorsPictureSource(DataSource):
    DEPUTIES_URL = "https://www.diputados.gov.ar/diputados/"
    SENATORS_URL = "https://www.senado.gob.ar/senadores/listados/listaSenadoRes"

    @classmethod
    def get_data(cls):
        senators_data = cls._get_senators_pictures()
        deputies_data = cls._get_deputies_pictures()
        legislators_data = senators_data + deputies_data
        df = pd.DataFrame(legislators_data)
        df[["last_name", "name"]] = df["raw_name"].str.split(",", expand=True)
        df = df.drop(columns=["raw_name"])
        return df

    @classmethod
    def _get_deputies_pictures(cls):
        response = requests.get(cls.DEPUTIES_URL)
        deputies_pictures = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"id": "tablaDiputados"})
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    picture_cell, name_cell = row.find_all(["th", "td"])[:2]
                    picture_url = picture_cell.find("img")["src"]
                    legislator_name = name_cell.get_text(strip=True)
                    info = {
                        "raw_name": legislator_name,
                        "picture_url": picture_url,
                    }
                    deputies_pictures.append(info)
        return deputies_pictures

    @classmethod
    def _get_senators_pictures(cls):
        response = requests.get(cls.SENATORS_URL)
        senators_pictures = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"id": "senadoresTabla"})
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    picture_cell, name_cell = row.find_all(["th", "td"])[:2]
                    picture_url = picture_cell.find("img")["data-src"]
                    picture_url = "https://www.senado.gob.ar" + picture_url
                    legislator_name = name_cell.get_text(strip=True)
                    try:
                        last_name, name = legislator_name.split(",")
                    except Exception as e:
                        # hot fixes lamentablemente
                        if "De Angeli" in legislator_name:
                            name, last_name = "Alfredo Luis", "De Angeli"
                        elif "di Tullio" in legislator_name:
                            name, last_name = "Juliana", "Di Tullio"
                        else:
                            raise e
                    name = name.replace("\n", "").strip()
                    last_name = last_name.replace("\n", "").strip()
                    full_name = f"{last_name}, {name}"
                    info = {
                        "raw_name": full_name,
                        "picture_url": picture_url,
                    }
                    senators_pictures.append(info)
        return senators_pictures
