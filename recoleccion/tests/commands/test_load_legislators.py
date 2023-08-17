from unittest.mock import PropertyMock, patch
from django.core.management import call_command
from recoleccion.components.linkers.linker import Linker

# Project
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class LegislatorsLoadingTestCase(LinkingTestCase):
    """
    This test case is meant to test the combined loading of both deputies and senators.
    """

    SENATE_CAPACITY = 72
    DEPUTIES_CAPACITY = 257

    def test_loading_senators_and_then_deputies(self):
        call_command("load_current_senators")
        call_command("load_current_deputies")
        total_active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR).count()
        total_active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY).count()
        self.assertEqual(total_active_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_active_deputies, self.DEPUTIES_CAPACITY)

    def test_loading_deputies_and_then_senators(self):
        call_command("load_current_deputies")
        call_command("load_current_senators")
        total_active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR).count()
        total_active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY).count()
        self.assertEqual(total_active_senators, self.SENATE_CAPACITY)
        self.assertEqual(total_active_deputies, self.DEPUTIES_CAPACITY)
