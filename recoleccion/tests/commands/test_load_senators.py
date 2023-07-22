from django.test import TestCase
from django.core.management import call_command

# Project
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat


class SenatorsLoadingTestCase(TestCase):
    SENATE_CAPACITY = 72

    def test_loading_senators_with_empty_database(self):
        call_command("load_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_persons, self.SENATE_CAPACITY)

    def test_loading_senators_with_already_loaded_db_and_no_changes(self):
        call_command("load_senators")
        call_command("load_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_persons, self.SENATE_CAPACITY)
    
    def test_loading_senators_with_already_loaded_db_and_changes(self):
        call_command("load_senators")
        changed_person = Person.objects.first()
        changed_person.name = "ImpossibleName"
        changed_person.last_name = "ImpossibleLastName"
        changed_person.save()
        call_command("load_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY + 1)
        self.assertEqual(total_persons, self.SENATE_CAPACITY + 1)
