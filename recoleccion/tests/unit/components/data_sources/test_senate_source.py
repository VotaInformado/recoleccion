from django.test import TestCase

# Project
from recoleccion.components.data_sources.senate_source import SenateHistory, CurrentSenate
import recoleccion.tests.test_helpers.mocks as mck


class SenateSourceTestCase(TestCase):
    def test_correct_senate_history_data_extraction(self):
        with mck.mock_method(CurrentSenate, "get_raw_data", mck.mock_data_source_csv("fake_current_deputies.csv")):
            senate_seats = SenateHistory().get_data()
        self.assertGreater(len(senate_seats), 0)

    def test_correct_current_senate_data_extraction(self):
        with mck.mock_method(CurrentSenate, "get_raw_data", mck.mock_data_source_json("fake_current_senate.json")):
            senate_seats = CurrentSenate().get_data()
        self.assertGreater(len(senate_seats), 0)
        senate_seats = SenateHistory().get_data()
        self.assertGreater(len(senate_seats), 0)
