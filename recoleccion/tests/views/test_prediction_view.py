import random
import requests
from django.core.management import call_command
from rest_framework.test import APITestCase

# Project
import recoleccion.tests.test_helpers.mocks as mck

from recoleccion.models import (
    LawProject,
    Person,
)
from recoleccion.utils.enums.project_chambers import ProjectChambers


class PredictionViewTestCase(APITestCase):
    fixtures = ["law_project.json", "person.json"]

    def test_legislator_prediction(self):
        person_id = Person.objects.first().id
        project_id = LawProject.objects.first().id
        payload = {
            "person_id": person_id,
            "law_project_id": project_id,
        }
        url = "/predictions/predict-legislator-vote/"
        with mck.mock_method(requests, "post", return_value=mck.mock_legislator_response(person_id)):
            response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["legislator"], person_id)

    def test_chamber_prediction(self):
        project_id = LawProject.objects.first().id
        chamber = random.choice([ProjectChambers.DEPUTIES, ProjectChambers.SENATORS])
        payload = {
            "chamber": chamber,
            "law_project_id": project_id,
        }
        url = "/predictions/predict-chamber-vote/"
        with mck.mock_method(requests, "post", return_value=mck.mock_chamber_response()):
            response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
