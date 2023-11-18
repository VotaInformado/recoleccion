import requests
from django.conf import settings

# Project
from recoleccion.models import LawProject, Person, Authorship
from recoleccion.serializers.law_projects import NeuralNetworkProjectSerializer
from recoleccion.serializers.authors import ReducedAuthorSerializer
from recoleccion.serializers.persons import ReducedPersonSerializer


class NeuralNetworkService:
    def __init__(self):
        self.base_url = settings.NEURAL_NETWORK_URL
        self.session = requests.Session()

    def get_active_legislators(self):
        return Person.objects.filter(is_active=True)

    def get_party_authors(self, project: LawProject):
        authors = Authorship.objects.filter(project=project)
        party_authors = [author.party for author in authors]
        authors_data = ReducedAuthorSerializer(party_authors, many=True).data
        return authors_data

    def get_legislators_data(self, legislator_id):
        if legislator_id:
            legislators = [Person.objects.get(id=legislator_id)]
        else:
            legislators = self.get_active_legislators()
        legislators_data = ReducedPersonSerializer(legislators, many=True).data
        return legislators_data

    def get_request_data(self, prediction_options: dict):
        project_id = prediction_options.get("project_id")
        legislator_id = prediction_options.get("legislator_id")
        project = LawProject.objects.get(id=project_id)
        legislators_data = self.get_legislators_data(legislator_id)
        authors_data = self.get_party_authors(project)
        project_data = NeuralNetworkProjectSerializer(project).data

        return {
            "authors": authors_data,
            "legislators": legislators_data,
            "project": project_data,
        }

    def get_url(self, prediction_options: dict):
        specific_legislator = prediction_options.get("legislator_id") is not None
        if specific_legislator:
            return f"{self.base_url}/predict-legislator-vote/"
        return f"{self.base_url}/predict-project-votes/"

    def get_prediction(self, prediction_options: dict):
        url = self.get_url(prediction_options)
        data = self.get_request_data(prediction_options)
        response = requests.post(url, json=data)
        return response.json()
