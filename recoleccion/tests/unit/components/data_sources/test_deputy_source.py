from django.test import TestCase
from recoleccion.components.data_sources import DeputiesHistory
from recoleccion.components.data_sources.deputy_source import DeputiesHistory, CurrentDeputies


class DeputySourceTestCase(TestCase):
    # def test_correct_deputies_history_data_extraction(self):
    # cambiaron todo el formato de como devuelven los datos los bobos estos
    #     deputy_seats = DeputiesHistory.get_data()
    #     self.assertGreater(len(deputy_seats), 0)

    def test_correct_current_deputies_data_extraction(self):
        current_deputies = CurrentDeputies.get_data()
        self.assertGreater(len(current_deputies), 0)
