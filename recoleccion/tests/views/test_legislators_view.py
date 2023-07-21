from rest_framework.test import APITestCase
from django.core.management import call_command
from recoleccion.models.person import Person

from recoleccion.models.senate_seat import SenateSeat


class LegislatorViewTestCase(APITestCase):

    def test_legislators_list_without_repeated_seats_senators(self):
        # Each legislator has had at most 1 seat in total
        call_command("load_senators")
        # Only senate_seats should be present
        url = "/legislators/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for person in response.json():
            legislator_seats = person["legislator_seats"]
            self.assertEquals(len(legislator_seats), 1)

    def test_legislators_list_without_repeated_seats_deputies(self):
        # Each legislator has had at most 1 seat in total
        call_command("load_deputies")
        # Only deputy_seats should be present
        url = "/legislators/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for person in response.json():
            legislator_seats = person["legislator_seats"]
            self.assertEquals(len(legislator_seats), 1)

    def test_legislators_list_with_repeated_sets(self):
        call_command("load_deputies")
        chosen_person = Person.objects.first()
        SenateSeat.objects.create(
            person_id=chosen_person.pk,
            province="Province",
            party="A party",
            start_of_term="2020-01-01",
            end_of_term="2024-01-01",
            is_active=False,
        )
        url = "/legislators/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for person in response.json():
            legislator_seats = person["legislator_seats"]
            if person["id"] == str(chosen_person.pk):
                self.assertEquals(len(legislator_seats), 2)
            else:
                self.assertEquals(len(legislator_seats), 1)
