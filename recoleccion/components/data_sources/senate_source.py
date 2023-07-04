import requests
import pandas as pd
from bs4 import BeautifulSoup

# Project
from recoleccion.components.data_sources import DataSource, Resource
from recoleccion.components.utils import clean_text_formatting


class SenateHistory(Resource):
    name = "SenateHistory"
    key = "ExportarListadoSenadoresHistorico"
    column_mappings = {
        "NOMBRE": "name",
        "APELLIDO": "last_name",
        "PROVINCIA": "province",
        "PARTIDO POLITICO O ALIANZA": "party",
        "INICIO PERIODO LEGAL": "start_of_term",
        "CESE PERIODO LEGAL": "end_of_term",
    }

    def clean_data(self, data):
        data[["APELLIDO", "NOMBRE"]] = data["SENADOR"].str.split(",", 1, expand=True)
        data = self.get_and_rename_relevant_columns(data)
        # Reemplazo los DNI en 0 por None para que no explote por duplicado
        data = data.replace(0, None)
        for column in ["name", "last_name", "province", "party"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        for column in ["start_of_term", "end_of_term"]:
            data[column] = pd.to_datetime(data[column], infer_datetime_format=True).dt.date
        return data


class SenateSource(DataSource):
    base_url = "https://www.senado.gob.ar/micrositios/DatosAbiertos"
    resources = [SenateHistory()]

    def get_resources(self):
        return self.resources

    def get_resource(self, resource):
        url = f"{self.base_url}/{resource.key}/json"
        response = requests.request("GET", url)
        soup = BeautifulSoup(response.text, features="html.parser")
        plain_text = soup.get_text()  # Obtengo el texto sin html
        rows = plain_text[plain_text.index("[") : plain_text.rfind("]") + 1]  # Me quedo solo con las filas
        return resource.clean_data(pd.read_json(rows, orient="records"))
