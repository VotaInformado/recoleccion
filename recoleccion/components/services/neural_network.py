import requests
from django.conf import settings

# Project
from recoleccion.models import LawProject, Person, Authorship
from recoleccion.serializers.law_projects import NeuralNetworkProjectSerializer
from recoleccion.serializers.persons import ReducedPersonSerializer



class NeuralNetworkService:
    def __init__(self):
        self.base_url = settings.NEURAL_NETWORK_URL
        self.session = requests.Session()

    def get_active_legislators(self, chamber: str):
        if chamber:
            return Person.objects.filter(is_active=True, last_seat=chamber)
        return Person.objects.filter(is_active=True)

    def get_party_authors(self, project: LawProject):
        authors = Authorship.objects.filter(project=project)
        party_authors = {author.party_id: True for author in authors}
        return [{"party": k} for k in party_authors.keys()]

    def get_legislator_data(self, legislator_id: int):
        legislator = Person.objects.get(id=legislator_id)
        legislator_data = ReducedPersonSerializer(legislator).data
        return legislator_data

    def get_legislators_data(self, legislators: list):
        legislators_data = ReducedPersonSerializer(legislators, many=True).data
        return legislators_data

    def get_legislator_request_data(self, prediction_options: dict):
        project_id = prediction_options.get("law_project_id")
        legislator_id = prediction_options.get("person_id")

        project = LawProject.objects.get(id=project_id)
        legislator_data = self.get_legislator_data(legislator_id)
        authors_data = self.get_party_authors(project)
        project_data = NeuralNetworkProjectSerializer(project).data
        return {
            "authors": authors_data,
            "legislator": legislator_data,
            "project": project_data,
        }

    def get_chamber_request_data(self, prediction_options: dict):
        chamber = prediction_options.get("chamber")
        project_id = prediction_options.get("law_project_id")
        legislators = self.get_active_legislators(chamber)
        legislators_data = self.get_legislators_data(legislators)
        project = LawProject.objects.get(id=project_id)
        authors_data = self.get_party_authors(project)
        project_data = NeuralNetworkProjectSerializer(project).data
        return {
            "authors": authors_data,
            "legislators": legislators_data,
            "project": project_data,
        }

    def get_legislator_prediction(self, prediction_options: dict):
        url = f"{self.base_url}/predict-legislator-vote/"
        data = self.get_legislator_request_data(prediction_options)
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(response.text)
        return response.json()

    def get_chamber_prediction(self, prediction_options: dict):
        url = f"{self.base_url}/predict-project-votes/"
        data = self.get_chamber_request_data(prediction_options)
        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(response.text)
        return response.json()
