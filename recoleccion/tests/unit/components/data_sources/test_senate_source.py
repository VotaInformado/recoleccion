from django.test import TestCase
from recoleccion.components.data_sources.senate_source import SenateHistory, CurrentSenate


class SenateSourceTestCase(TestCase):
    def test_correct_senate_history_data_extraction(self):
        senate_seats = SenateHistory().get_data()
        self.assertGreater(len(senate_seats), 0)

    def test_correct_current_senate_data_extraction(self):
        senate_seats = SenateHistory().get_data()
        self.assertGreater(len(senate_seats), 0)
