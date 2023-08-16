from unittest.mock import PropertyMock, patch
from django.test import TestCase
from django.core.management import call_command
from recoleccion.components.linkers.linker import Linker

# Project
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class LegislatorsLoadingTestCase(TestCase):
    """
    This test case is meant to test the combined loading of both deputies and senators.
    """

    SENATE_CAPACITY = 72
    DEPUTIES_CAPACITY = 257

    def test_loading_senators_and_then_deputies(self):
        with patch.object(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
            attr_mock.return_value = "recoleccion/components/linkers/training/tests"
            call_command("load_current_senators")
            call_command("load_current_deputies")
        total_active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR).count()
        total_active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY).count()
        self.assertEqual(total_active_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_active_deputies, self.DEPUTIES_CAPACITY)

    def test_loading_deputies_and_then_senators(self):
        with patch.object(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
            attr_mock.return_value = "recoleccion/components/linkers/training/tests"
            call_command("load_current_deputies")
            call_command("load_current_senators")
        total_active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR).count()
        total_active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY).count()
        self.assertEqual(total_active_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_active_deputies, self.DEPUTIES_CAPACITY)
