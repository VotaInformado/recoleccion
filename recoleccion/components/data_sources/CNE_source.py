import requests
import pandas as pd
from rarfile import RarFile
from io import BytesIO

# Project
from recoleccion.components.data_sources import DataSource, Resource
from recoleccion.components.utils import clean_text_formatting


class Candidacies(Resource):
    name = "Candidacies"
    key = "candidaturas2021.rar"
    column_mappings = {
        "DNI": "dni",
        "Nombres": "name",
        "Apellido": "last_name",
        "Fecha Nacimiento": "birthdate",
        "Genero": "gender",
    }

    def clean_data(self, data):
        data = self.get_and_rename_relevant_columns(data)
        # Reemplazo los DNI en 0 por None para que no explote por duplicado
        data.loc[data["dni"] == 0, "dni"] = None
        data.loc[data["name"] == 0, "name"] = None
        data.loc[data["last_name"] == 0, "last_name"] = None
        for column in ["name", "last_name", "gender"]:
            data[column] = data[column].map(clean_text_formatting).astype(str)
        return data


class CNESource(DataSource):
    base_url = "https://www.electoral.gob.ar/nuevo/paginas/datos/"
    resources = [
        Candidacies(),
    ]

    def get_resources(self):
        return self.resources

    def get_resource(self, resource):
        url = f"{self.base_url}/{resource.key}"
        response = requests.request("GET", url)
        # Extract rar file and return file
        with RarFile(BytesIO(response.content)) as rf:
            for file in rf.infolist():
                if file.filename.endswith(".csv"):
                    with rf.open(file) as f:
                        return resource.clean_data(pd.read_csv(f, sep=";"))
                if file.filename.endswith(".xlsx"):
                    with rf.open(file) as f:
                        return resource.clean_data(pd.read_excel(f))
