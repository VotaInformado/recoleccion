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
        chosen_legislator = Person.objects.filter(last_seat__isnull=False).first()
        project_id = LawProject.objects.first().id
        payload = {
            "person_id": chosen_legislator.pk,
            "law_project_id": project_id,
        }
        url = "/predictions/predict-legislator-vote/"
        with mck.mock_method(requests, "post", return_value=mck.mock_legislator_response(chosen_legislator.pk)):
            response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        response_legislator_id = response.data["legislator"]["id"]
        response_legislator_name = response.data["legislator"]["name"]
        response_legislator_last_name = response.data["legislator"]["last_name"]
        response_legislator_last_seat = response.data["legislator"]["last_seat"]
        self.assertEqual(response_legislator_id, chosen_legislator.pk)
        self.assertEqual(response_legislator_name, chosen_legislator.name)
        self.assertEqual(response_legislator_last_name, chosen_legislator.last_name)
        self.assertEqual(response_legislator_last_seat, chosen_legislator.last_seat)

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

    def test_chamber_prediction_for_both_chambers(self):
        project_id = LawProject.objects.first().id
        payload = {
            "law_project_id": project_id,
        }
        url = "/predictions/predict-chamber-vote/"
        with mck.mock_method(requests, "post", return_value=mck.mock_chamber_response()):
            response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
