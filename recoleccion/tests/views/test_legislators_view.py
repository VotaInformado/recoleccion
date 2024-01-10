import random
from django.core.management import call_command
from django.db import transaction
from recoleccion.models.deputy_seat import DeputySeat

# Project
from recoleccion.models.law_project import LawProject
from recoleccion.models.vote import Vote
from recoleccion.tests.test_helpers.test_case import LinkingAPITestCase
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
from recoleccion.utils.enums.vote_choices import VoteChoices


class LegislatorViewTestCase(LinkingAPITestCase):
    def test_legislators_list_without_repeated_seats_senators(self):
        # Each legislator has had at most 1 seat in total
        call_command("load_current_senators")
        # Only senate_seats should be present
        url = "/legislators/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for person in response.json():
            last_seat = person["last_seat"]
            self.assertEquals(last_seat, LegislatorSeats.SENATOR.label)

    def test_legislators_list_without_repeated_seats_deputies(self):
        # Each legislator has had at most 1 seat in total
        call_command("load_current_deputies")
        # Only deputy_seats should be present
        url = "/legislators/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for person in response.json():
            last_seat = person["last_seat"]
            self.assertEquals(last_seat, LegislatorSeats.DEPUTY.label)

    def test_simple_legislators_retrieval(self):
        call_command("load_current_deputies")
        chosen_person = Person.objects.first()
        url = f"/legislators/{chosen_person.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        keys = list(data.keys())
        self.assertEqual(data["id"], chosen_person.pk)
        self.assertEqual(data["name"], chosen_person.name)
        self.assertEqual(data["last_name"], chosen_person.last_name)
        self.assertEqual(
            data["last_seat"], LegislatorSeats(chosen_person.last_seat).label
        )
        legislator_seats = data["legislator_seats"]
        self.assertEquals(len(legislator_seats), 1)

    def test_legislators_retrieval_with_repeated_seats(self):
        call_command("load_current_deputies")
        chosen_person = Person.objects.first()
        SenateSeat.objects.create(
            person_id=chosen_person.pk,
            province="Province",
            party_name="A party",
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        url = f"/legislators/{chosen_person.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        legislator_seats = data["legislator_seats"]
        self.assertEquals(data["id"], chosen_person.pk)
        self.assertEquals(len(legislator_seats), 2)

    def create_votes(self, total_votes, person):
        chamber = "SENATORS"
        date = "2020-01-01"
        projects = LawProject.objects.filter(senate_project_id__isnull=False).all()[
            :total_votes
        ]
        with transaction.atomic():
            for i in range(total_votes):
                Vote.objects.create(
                    chamber=chamber,
                    date=date,
                    person=person,
                    project=projects[i],
                    vote=random.choice(VoteChoices.values),
                )

    def test_legislator_votes_retrieval(self):
        EXPECTED_VOTES = 10
        call_command("loaddata", "person.json")
        call_command("loaddata", "law_project.json")
        chosen_person = Person.objects.first()
        DeputySeat.objects.create(
            person_id=chosen_person.pk,
            district="Province",
            party_name="A party",
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
        )
        self.create_votes(EXPECTED_VOTES, chosen_person)
        url = f"/legislators/{chosen_person.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        votes = data["votes"]

        self.assertIn("afirmatives", votes)
        self.assertIn("negatives", votes)
        self.assertIn("abstentions", votes)
        self.assertIn("absents", votes)
