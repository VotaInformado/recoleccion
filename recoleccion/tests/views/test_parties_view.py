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
                party=party, denomination=sub_party_name, relation_type=PartyRelationTypes.SUB_PARTY
            )
        return party

    def test_party_list(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = ["Partido Justicialista de Mendoza", "Part. Justicialista - Buenos Aires"]
        party = self.create_party_and_denominations()
        URL = "/parties/"
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 1)
        response_party = response_content[0]
        self.assertEqual(response_party["main_denomination"], self.MAIN_DENOMINATION)
        response_alternative_denominations = response_party["alternative_denominations"]
        self.assertEqual(len(response_alternative_denominations), len(self.ALTERNATIVE_DENOMINATIONS))
        self.assertEqual(sorted(response_alternative_denominations), sorted(self.ALTERNATIVE_DENOMINATIONS))
        response_sub_parties = response_party["sub_parties"]
        self.assertEqual(len(response_sub_parties), len(self.SUB_PARTIES))
        self.assertEqual(sorted(response_sub_parties), sorted(self.SUB_PARTIES))

    def test_party_retrieval(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = ["Partido Justicialista de Mendoza", "Part. Justicialista - Buenos Aires"]
        party = self.create_party_and_denominations()
        deputy = Person.objects.create(name="Juan", last_name="Perez")
        senator = Person.objects.create(name="Pedro", last_name="Gomez")
        voter = Person.objects.create(name="Maria", last_name="Gomez")
        law_project = LawProject.objects.create(title="Some title", origin_chamber="DEPUTIES")
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        deputy_seat = DeputySeat.objects.create(
            person=deputy, party=party, start_of_term="2020-01-01", end_of_term="2024-01-01"
        )
        senate_seat = SenateSeat.objects.create(
            person=senator, party=party, start_of_term="2020-01-01", end_of_term="2024-01-01"
        )
        vote = Vote.objects.create(person=voter, party=party)
        authorship = Authorship.objects.create(person=author, party=party, law_project=law_project)
        URL = f"/parties/{party.pk}/"
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(response_content["main_denomination"], self.MAIN_DENOMINATION)
        response_alternative_denominations = response_content["alternative_denominations"]
        self.assertEqual(len(response_alternative_denominations), len(self.ALTERNATIVE_DENOMINATIONS))
        self.assertEqual(sorted(response_alternative_denominations), sorted(self.ALTERNATIVE_DENOMINATIONS))
        response_sub_parties = response_content["sub_parties"]
        self.assertEqual(len(response_sub_parties), len(self.SUB_PARTIES))
        self.assertEqual(sorted(response_sub_parties), sorted(self.SUB_PARTIES))
        response_members = response_content["members"]
        sorted_response_members = sorted(response_members, key=lambda x: x["id"])
        response_member_ids = [member["id"] for member in sorted_response_members]
        response_member_objects = [Person.objects.get(pk=member_id) for member_id in response_member_ids]
        self.assertEqual(len(response_members), 4)
        expected_members = [deputy, senator, voter, author]
        sorted_expected_members = sorted(expected_members, key=lambda x: x.pk)
        self.assertEqual(response_member_objects, sorted_expected_members)
