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
from recoleccion.utils.enums.provinces import Provinces


class PartiesViewTestCase(APITestCase):
    fixtures = ["law_project.json", "person.json"]

    def setUp(self):
        self.MAIN_DENOMINATION = "Partido Justicialista"
        self.ALTERNATIVE_DENOMINATIONS = ["Part. Justicialista", "Justicialismo"]
        self.SUB_PARTIES = [
            "Partido Justicialista de Mendoza",
            "Part. Justicialista - Buenos Aires",
        ]
        self.party = self.create_party_and_denominations(
            self.MAIN_DENOMINATION, self.ALTERNATIVE_DENOMINATIONS, self.SUB_PARTIES
        )
        self.extra_party = self.create_party_and_denominations("Otro partido")

    def create_party_and_denominations(
        self, party_denomination, alternative_denominations=[], sub_parties=[]
    ):
        party = Party.objects.create(main_denomination=party_denomination)
        for denomination in alternative_denominations:
            PartyDenomination.objects.create(
                party=party,
                denomination=denomination,
                relation_type=PartyRelationTypes.ALTERNATIVE_DENOMINATION,
            )
        for sub_party_name in sub_parties:
            PartyDenomination.objects.create(
                party=party,
                denomination=sub_party_name,
                relation_type=PartyRelationTypes.SUB_PARTY,
            )
        return party

    def test_party_list(self):
        URL = "/parties/"
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        response_content = response.json()
        self.assertEqual(len(response_content), 2)  # party and extra_party
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
        deputy = Person.objects.create(name="Juan", last_name="Perez")
        senator = Person.objects.create(name="Pedro", last_name="Gomez")
        voter = Person.objects.create(name="Maria", last_name="Gomez")
        law_project = LawProject.objects.create(
            title="Some title", origin_chamber="DEPUTIES"
        )
        author = Person.objects.create(name="Roberto", last_name="Suárez")
        deputy_seat = DeputySeat.objects.create(
            person=deputy,
            party=self.party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        senate_seat = SenateSeat.objects.create(
            person=senator,
            party=self.party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        vote = Vote.objects.create(person=voter, party=self.party)
        authorship = Authorship.objects.create(
            person=author, party=self.party, project=law_project
        )
        URL = f"/parties/{self.party.pk}/"
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
        self.assertEqual(response_content["total_legislators"], 4)

    def create_party_votes_for_project(
        self, law_project, total_votes, add_extra_party_votes=True
    ):
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
        if add_extra_party_votes:
            EXTRA_PARTY_VOTES = 10
            for i in range(EXTRA_PARTY_VOTES):
                person = random.choice(persons)
                persons.remove(person)
                vote_choice = random.choice(vote_choices)
                Vote.objects.create(
                    chamber=chamber,
                    date=date,
                    person=person,
                    project=law_project,
                    vote=vote_choice,
                    party=self.extra_party,
                )

    def test_retrieving_party_votes_with_limited_results(self):
        TOTAL_PROJECTS_WITH_VOTES = 10
        TOTAL_VOTES = 50
        MAX_RESULTS = 5
        self.projects = list(LawProject.objects.all())
        self.chosen_project_titles = []
        for i in tqdm(range(TOTAL_PROJECTS_WITH_VOTES)):
            law_project = random.choice(self.projects)
            self.projects.remove(law_project)
            self.chosen_project_titles.append(law_project.title)
            self.create_party_votes_for_project(law_project, TOTAL_VOTES)
        url = f"/parties/{self.party.pk}/votes/"
        response = self.client.get(url + f"?page=1&page_size={MAX_RESULTS}")
        self.assertEqual(response.status_code, 200)
        law_projects = response.json()["results"]
        self.assertEqual(len(law_projects), MAX_RESULTS)
        for retrieved_project in law_projects:
            self.assertIn(retrieved_project["title"], self.chosen_project_titles)
            self.assertEqual(retrieved_project["total_votes"], TOTAL_VOTES)

    def test_retrieving_party_votes_with_full_results(self):
        TOTAL_PROJECTS_WITH_VOTES = 20
        TOTAL_VOTES = 50
        PAGE_SIZE = 10
        self.projects = list(LawProject.objects.all())
        self.chosen_project_titles = []
        for i in tqdm(range(TOTAL_PROJECTS_WITH_VOTES)):
            law_project = random.choice(self.projects)
            self.projects.remove(law_project)
            self.chosen_project_titles.append(law_project.title)
            self.create_party_votes_for_project(law_project, TOTAL_VOTES)
        url = f"/parties/{self.party.pk}/votes/"
        params = {"page_size": PAGE_SIZE}
        received_data = []
        while True:
            response = self.client.get(url, data=params)
            self.assertEqual(response.status_code, 200)
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break
        self.assertEqual(len(received_data), TOTAL_PROJECTS_WITH_VOTES)
        for project in received_data:
            self.assertIn(project["title"], self.chosen_project_titles)
            self.assertEqual(project["total_votes"], TOTAL_VOTES)

    def create_new_party(self, party_name: str):
        return self.create_party_and_denominations(party_name)

    def test_retrieving_party_votes_when_the_party_has_no_votes(self):
        TOTAL_PROJECTS_WITH_VOTES = 20
        TOTAL_VOTES = 50
        PAGE_SIZE = 10
        EXPECTED_PARTY_PROJECTS = 0
        self.projects = list(LawProject.objects.all())
        self.chosen_project_titles = []
        for i in tqdm(range(TOTAL_PROJECTS_WITH_VOTES)):
            law_project = random.choice(self.projects)
            self.projects.remove(law_project)
            self.chosen_project_titles.append(law_project.title)
            self.create_party_votes_for_project(law_project, TOTAL_VOTES)
        new_party = self.create_new_party("Nuevo Partido")
        url = f"/parties/{new_party.pk}/votes/"
        params = {"page_size": PAGE_SIZE}
        received_data = []
        while True:
            response = self.client.get(url, data=params)
            self.assertEqual(response.status_code, 200)
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None
            if url is None:
                break
        self.assertEqual(len(received_data), EXPECTED_PARTY_PROJECTS)

    def test_get_country_representation(self):
        party = self.create_new_party("Nuevo Partido")
        deputy = Person.objects.create(name="Juan", last_name="Perez")
        DeputySeat.objects.create(
            person=deputy,
            party=party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
            district=Provinces.FORMOSA.value,
        )
        SenateSeat.objects.create(
            person=deputy,
            party=party,
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
            province=Provinces.CORDOBA.value,
        )
        response = self.client.get(f"/parties/{party.pk}/")

        self.assertEqual(response.status_code, 200)
        response_content = response.json()

        formosa_values = response_content["country_representation"][
            Provinces.FORMOSA.value
        ]
        self.assertEqual(formosa_values["senate_seats"], 0)
        self.assertEqual(formosa_values["deputy_seats"], 1)
        self.assertEqual(formosa_values["total_members"], 1)
        self.assertEqual(formosa_values["province_name"], Provinces.FORMOSA.label)
        cordoba_values = response_content["country_representation"][
            Provinces.CORDOBA.value
        ]
        self.assertEqual(cordoba_values["senate_seats"], 1)
        self.assertEqual(cordoba_values["deputy_seats"], 0)
        la_rioja_values = response_content["country_representation"][
            Provinces.LA_RIOJA.value
        ]
        self.assertEqual(la_rioja_values["senate_seats"], 0)
        self.assertEqual(la_rioja_values["deputy_seats"], 0)
        self.assertEqual(la_rioja_values["total_members"], 0)


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
