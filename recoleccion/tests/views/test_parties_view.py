import random
from tqdm import tqdm
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
    VoteSession,
)
from recoleccion.utils.enums.vote_choices import VoteChoices
from recoleccion.utils.enums.project_chambers import ProjectChambers


class PartiesViewTestCase(APITestCase):
    fixtures = ["law_project.json", "person.json"]

    def setUp(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = ["Partido Justicialista de Mendoza", "Part. Justicialista - Buenos Aires"]
        self.party = self.create_party_and_denominations()

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
        deputy = Person.objects.create(name="Juan", last_name="Perez")
        senator = Person.objects.create(name="Pedro", last_name="Gomez")
        voter = Person.objects.create(name="Maria", last_name="Gomez")
        law_project = LawProject.objects.create(title="Some title", origin_chamber="DEPUTIES")
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        deputy_seat = DeputySeat.objects.create(
            person=deputy, party=self.party, start_of_term="2020-01-01", end_of_term="2024-01-01"
        )
        senate_seat = SenateSeat.objects.create(
            person=senator, party=self.party, start_of_term="2020-01-01", end_of_term="2024-01-01"
        )
        vote = Vote.objects.create(person=voter, party=self.party)
        authorship = Authorship.objects.create(person=author, party=self.party, project=law_project)
        URL = f"/parties/{self.party.pk}/"
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
        # response_members = response_content["members"]
        # sorted_response_members = sorted(response_members, key=lambda x: x["id"])
        # response_member_ids = [member["id"] for member in sorted_response_members]
        # response_member_objects = [Person.objects.get(pk=member_id) for member_id in response_member_ids]
        self.assertEqual(response_content["total_members"], 4)
        # expected_members = [deputy, senator, voter, author]
        # sorted_expected_members = sorted(expected_members, key=lambda x: x.pk)
        # self.assertEqual(response_member_objects, sorted_expected_members)

    def create_party_votes_for_project(self, law_project, total_votes):
        vote_choices = list(VoteChoices.values)
        vote_choices.remove("PRESIDENT")
        chamber = random.choice(ProjectChambers.values)
        date = "2020-01-01"
        persons = list(Person.objects.all())
        for i in range(total_votes):
            person = random.choice(persons)
            persons.remove(person)
            vote_choice = random.choice(vote_choices)
            Vote.objects.create(
                chamber=chamber,
                date=date,
                person=person,
                project=law_project,
                vote=vote_choice,
                party=self.party,
            )

    def test_retrieving_party_votes(self):
        TOTAL_PROJECTS_WITH_VOTES = 10
        TOTAL_VOTES = 50
        self.projects = list(LawProject.objects.all())
        self.chosen_project_titles = []
        for i in tqdm(range(TOTAL_PROJECTS_WITH_VOTES)):
            law_project = random.choice(self.projects)
            self.projects.remove(law_project)
            self.chosen_project_titles.append(law_project.title)
            self.create_party_votes_for_project(law_project, TOTAL_VOTES)
        url = f"/parties/{self.party.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for retrieved_project in response.json()["party_votes"]:
            self.assertIn(retrieved_project["project_title"], self.chosen_project_titles)
            self.assertEqual(retrieved_project["total_votes"], TOTAL_VOTES)
