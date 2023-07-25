from django.test import TestCase
from django.core.management import call_command

# Project
from recoleccion.components.data_sources.deputy_source import CurrentDeputies, DeputiesHistory
from recoleccion.components.writers.persons_writer import PersonsWriter
from recoleccion.management.commands.load_current_deputies import Command as LoadCurrentDeputiesCommand
from recoleccion.management.commands.load_deputies_history import Command as LoadDeputiesHistoryCommand
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.models.person import Person
from recoleccion.models import DeputySeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class DeputiesLoadingTestCase(TestCase):
    DEPUTIES_CAPACITY = 257

    def test_loading_deputies_with_empty_database(self):
        call_command("load_current_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY)

    def test_loading_deputies_with_already_loaded_db_and_no_changes(self):
        call_command("load_current_deputies")
        call_command("load_current_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY)

    def test_loading_deputies_with_already_loaded_db_and_changes(self):
        call_command("load_current_deputies")
        changed_person = Person.objects.first()
        changed_person.name = "ImpossibleName"
        changed_person.last_name = "ImpossibleLastName"
        changed_person.save()
        call_command("load_current_deputies")
        total_deputies = DeputySeat.objects.count()
        total_persons = Person.objects.count()
        self.assertEqual(total_deputies, self.DEPUTIES_CAPACITY + 1)
        self.assertEqual(total_persons, self.DEPUTIES_CAPACITY + 1)

    def test_loading_deputies_last_seat(self):
        call_command("load_current_deputies")
        any_person = Person.objects.first()
        self.assertEqual(any_person.last_seat, LegislatorSeats.DEPUTY)

    def test_loading_deputies_history_with_current_deputies_loaded(self):
        # The files are created so that there is a deputy that has been in two seats
        DEPUTY_NAME = "Hilda Clelia"
        DEPUTY_LAST_NAME = "Aguirre"
        mocked_deputies = mck.get_file_data_length("fake_current_deputies.csv")
        with mck.mock_method(PersonsWriter, "update_active_persons", return_value=None):
            with mck.mock_class_attribute(LoadCurrentDeputiesCommand, "DEPUTIES_CAPACITY", mocked_deputies):
                with mck.mock_class_attribute(LoadDeputiesHistoryCommand, "DEPUTIES_CAPACITY", mocked_deputies):
                    with mck.mock_method(CurrentDeputies, "get_raw_data", mck.mock_data_source_csv("fake_current_deputies.csv")):
                        with mck.mock_method(DeputiesHistory, "get_raw_data", mck.mock_data_source_csv("fake_deputies_history.csv")):
                            call_command("load_current_deputies")
                            call_command("load_deputies_history")
        deputy = Person.objects.get(name=DEPUTY_NAME, last_name=DEPUTY_LAST_NAME)
        self.assertTrue(deputy.is_active)
        deputy_seats = DeputySeat.objects.filter(person=deputy)
        self.assertEqual(len(deputy_seats), 2)
