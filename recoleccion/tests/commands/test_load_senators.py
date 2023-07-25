from django.test import TestCase
from django.core.management import call_command
import requests

# Project
from recoleccion.components.writers.persons_writer import PersonsWriter
from recoleccion.management.commands.load_current_senators import Command as LoadCurrentSenatorsCommand
from recoleccion.management.commands.load_senators_history import Command as LoadSenatorsHistoryCommand
from recoleccion.components.data_sources.senate_source import CurrentSenate, SenateHistory
from recoleccion.exceptions.custom import SenateLoadingException
from recoleccion.models.deputy_seat import DeputySeat
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
import recoleccion.tests.test_helpers.mocks as mck


class CurrentSenatorsLoadingTestCase(TestCase):
    SENATE_CAPACITY = 72

    def test_loading_senators_with_empty_database(self):
        call_command("load_current_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_persons, self.SENATE_CAPACITY)

    def test_loading_senators_with_already_loaded_db_and_no_changes(self):
        call_command("load_current_senators")
        call_command("load_current_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_persons, self.SENATE_CAPACITY)

    def test_loading_senators_with_already_loaded_db_and_changes(self):
        call_command("load_current_senators")
        changed_person = Person.objects.first()
        changed_person.name = "ImpossibleName"
        changed_person.last_name = "ImpossibleLastName"
        changed_person.save()
        call_command("load_current_senators")
        total_senators = SenateSeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_senators, self.SENATE_CAPACITY + 1)
        self.assertEqual(total_persons, self.SENATE_CAPACITY + 1)

    def test_loading_senators_last_seat(self):
        call_command("load_current_senators")
        any_person = Person.objects.first()
        self.assertEqual(any_person.last_seat, LegislatorSeats.SENATOR)


class SenatorHistoryLoadingTestCase(TestCase):
    SENATE_CAPACITY = 72

    def test_loading_senators_history_with_empty_database_raises_exception(self):
        with self.assertRaises(SenateLoadingException):
            call_command("load_senators_history")

    def test_loading_senators_history_with_incorrect_active_senators_raises_exception(self):
        call_command("load_current_senators")
        changed_person = Person.objects.first()
        changed_person.is_active = False
        changed_person.save()
        with self.assertRaises(SenateLoadingException):
            call_command("load_senators_history")

    def test_loading_senators_history_with_current_senators_loaded(self):
        SENATOR_NAME = "Stella Maris"
        SENATOR_LAST_NAME = "Olalla"
        mocked_senators = mck.get_file_data_length("fake_current_senate.json")
        with mck.mock_method(PersonsWriter, "update_active_persons", return_value=None):
            with mck.mock_class_attribute(LoadCurrentSenatorsCommand, "SENATE_CAPACITY", mocked_senators):
                with mck.mock_class_attribute(LoadSenatorsHistoryCommand, "SENATE_CAPACITY", mocked_senators):
                    with mck.mock_method(
                        CurrentSenate, "get_raw_data", mck.mock_data_source_json("fake_current_senate.json")
                    ):
                        with mck.mock_method(
                            SenateHistory, "get_raw_data", mck.mock_data_source_json("fake_senate_history.json")
                        ):
                            call_command("load_current_senators")
                            call_command("load_senators_history")
        senator = Person.objects.get(name=SENATOR_NAME, last_name=SENATOR_LAST_NAME)
        self.assertTrue(senator.is_active)
        senator_seats = SenateSeat.objects.filter(person=senator)
        self.assertEqual(len(senator_seats), 2)
