from django.test import TestCase
from recoleccion.components.data_sources import DeputyHistory
from recoleccion.components.data_sources.deputy_source import DeputyHistory, CurrentDeputies


class DeputySourceTestCase(TestCase):
    def test_correct_deputies_history_data_extraction(self):
        deputy_seats = DeputyHistory.get_data()
        self.assertGreater(len(deputy_seats), 0)

    def test_correct_current_deputies_data_extraction(self):
        current_deputies = CurrentDeputies.get_data()
        self.assertGreater(len(current_deputies), 0)
