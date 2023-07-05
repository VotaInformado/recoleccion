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
        "nombre": "name",
        "apellido": "last_name",
        "provincia": "province",
        "partido politico o alianza": "party",
        "inicio periodo legal": "start_of_term",
        "cese periodo legal": "end_of_term",
    }

    def clean_data(self, data: pd.DataFrame):
        data.columns = [column.lower() for column in data.columns]
        data[["apellido", "nombre"]] = data["senador"].str.split(",", n=1, expand=True)
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
