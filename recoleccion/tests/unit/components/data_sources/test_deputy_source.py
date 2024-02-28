from django.test import TestCase

# Project
from recoleccion.components.data_sources.deputy_source import CurrentDeputies
import recoleccion.tests.test_helpers.mocks as mck


class DeputySourceTestCase(TestCase):
    def test_correct_current_deputies_data_extraction(self):
        with mck.mock_method(CurrentDeputies, "get_raw_data", mck.mock_data_source_csv("fake_current_deputies.csv")):
            current_deputies = CurrentDeputies.get_data()
        self.assertGreater(len(current_deputies), 0)
