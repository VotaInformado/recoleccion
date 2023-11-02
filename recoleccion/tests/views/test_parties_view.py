import random
from django.core.management import call_command
from django.db import transaction
from rest_framework.test import APITestCase

# Project
from recoleccion.models import (
    Authorship,
    DeputySeat,
    LawProject,
    Party,
    PartyDenomination,
    PartyRelationTypes,
    Person,
    SenateSeat,
    Vote,
)


class PartiesViewTestCase(APITestCase):
    def create_party_and_denominations(self):
        party = Party.objects.create(main_denomination=self.MAIN_DENOMINATION)
        for denomination in self.ALTERNATIVE_DENOMINATIONS:
            PartyDenomination.objects.create(
                party=party,
                denomination=denomination,
                relation_type=PartyRelationTypes.ALTERNATIVE_DENOMINATION,
            )
        for sub_party_name in self.SUB_PARTIES:
            PartyDenomination.objects.create(
                party=party,
                denomination=sub_party_name,
                relation_type=PartyRelationTypes.SUB_PARTY,
            )
        return party

    def test_party_list(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = [
            "Partido Justicialista de Mendoza",
            "Part. Justicialista - Buenos Aires",
        ]
        party = self.create_party_and_denominations()
        URL = "/parties/"
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 1)
        response_party = response_content[0]
        self.assertEqual(response_party["main_denomination"], self.MAIN_DENOMINATION)
        response_alternative_denominations = response_party["alternative_denominations"]
        self.assertEqual(
            len(response_alternative_denominations), len(self.ALTERNATIVE_DENOMINATIONS)
        )
        self.assertEqual(
            sorted(response_alternative_denominations),
            sorted(self.ALTERNATIVE_DENOMINATIONS),
        )
        response_sub_parties = response_party["sub_parties"]
        self.assertEqual(len(response_sub_parties), len(self.SUB_PARTIES))
        self.assertEqual(sorted(response_sub_parties), sorted(self.SUB_PARTIES))

    def test_party_retrieval(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = [
            "Partido Justicialista de Mendoza",
            "Part. Justicialista - Buenos Aires",
        ]
        party = self.create_party_and_denominations()
        deputy = Person.objects.create(name="Juan", last_name="Perez")
        senator = Person.objects.create(name="Pedro", last_name="Gomez")
        voter = Person.objects.create(name="Maria", last_name="Gomez")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        deputy_seat = DeputySeat.objects.create(
            person=deputy,
            party=party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        senate_seat = SenateSeat.objects.create(
            person=senator,
            party=party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        vote = Vote.objects.create(person=voter, party=party)
        authorship = Authorship.objects.create(
            person=author, party=party, project=law_project
        )
        URL = f"/parties/{party.pk}/"
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(response_content["main_denomination"], self.MAIN_DENOMINATION)
        response_alternative_denominations = response_content[
            "alternative_denominations"
        ]
        self.assertEqual(
            len(response_alternative_denominations), len(self.ALTERNATIVE_DENOMINATIONS)
        )
        self.assertEqual(
            sorted(response_alternative_denominations),
            sorted(self.ALTERNATIVE_DENOMINATIONS),
        )
        response_sub_parties = response_content["sub_parties"]
        self.assertEqual(len(response_sub_parties), len(self.SUB_PARTIES))
        self.assertEqual(sorted(response_sub_parties), sorted(self.SUB_PARTIES))
        self.assertEqual(response_content["total_members"], 4)


class PartiesAuthorsProjectsCountViewTestCase(APITestCase):
    def test_author_projects_count_is_correct(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        Authorship.objects.create(person=author, party=party, project=law_project)
        URL = f"/parties/{party.pk}/authorships/"
        response = self.client.get(URL)

        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 1)
        authorship_count = response_content[0]
        self.assertEqual(authorship_count["authorship_count"], 1)
        self.assertEqual(authorship_count["person"]["id"], author.pk)
        self.assertEqual(authorship_count["person"]["name"], author.name)

    def test_if_no_authorships_for_person_it_is_not_included(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        response = self.client.get(f"/parties/{party.pk}/authorships/")

        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 0)

    def test_two_authors_for_the_same_project_count_is_correct(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        author2 = Person.objects.create(name="Juan", last_name="Perez")
        Authorship.objects.create(person=author, party=party, project=law_project)
        Authorship.objects.create(person=author2, party=party, project=law_project)
        response = self.client.get(f"/parties/{party.pk}/authorships/")

        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 2)
        self.assertEqual(response_content[0]["authorship_count"], 1)
        self.assertEqual(response_content[1]["authorship_count"], 1)
        self.assertEqual(response_content[0]["person"]["id"], author.pk)
        self.assertEqual(response_content[1]["person"]["id"], author2.pk)

    def test_author_of_multiple_projects_count_is_correct(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        law_project2 = LawProject.objects.create(
            title="Some title 2", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        Authorship.objects.create(person=author, party=party, project=law_project)
        Authorship.objects.create(person=author, party=party, project=law_project2)
        response = self.client.get(f"/parties/{party.pk}/authorships/")

        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 1)
        self.assertEqual(response_content[0]["authorship_count"], 2)
        self.assertEqual(response_content[0]["person"]["id"], author.pk)

    def test_response_is_ordered_by_authorship_count_descending(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        law_project2 = LawProject.objects.create(
            title="Some title 2", origin_chamber="DEPUTIES"
        )
        author2 = Person.objects.create(name="Juan", last_name="Perez")
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        Authorship.objects.create(person=author2, party=party, project=law_project)
        Authorship.objects.create(person=author, party=party, project=law_project)
        Authorship.objects.create(person=author, party=party, project=law_project2)

        response = self.client.get(f"/parties/{party.pk}/authorships/")
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 2)
        self.assertEqual(response_content[0]["authorship_count"], 2)
        self.assertEqual(response_content[0]["person"]["id"], author.pk)
