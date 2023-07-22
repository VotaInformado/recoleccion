from django.test import TestCase
from django.core.management import call_command

# Project

from recoleccion.models.person import Person
from recoleccion.models import DeputySeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class DeputiesLoadingTestCase(TestCase):
    DEPUTIES_CAPACITY = 257

    def test_loading_deputies_with_empty_database(self):
        call_command("load_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY)

    def test_loading_deputies_with_already_loaded_db_and_no_changes(self):
        call_command("load_deputies")
        call_command("load_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY)
    
    def test_loading_deputies_with_already_loaded_db_and_changes(self):
        call_command("load_deputies")
        changed_person = Person.objects.first()
        changed_person.name = "ImpossibleName"
        changed_person.last_name = "ImpossibleLastName"
        changed_person.save()
        call_command("load_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY + 1)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY + 1)
    
    def test_loading_deputies_last_seat(self):
        call_command("load_deputies")
        any_person = Person.objects.first()
        self.assertEqual(any_person.last_seat, LegislatorSeats.DEPUTY)
