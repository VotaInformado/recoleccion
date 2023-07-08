from django.test import TestCase

from recoleccion.components.data_sources import DeputySource
from recoleccion.components.data_sources.deputy_source import DeputyHistory
from recoleccion.components.data_sources.senate_source import SenateHistory, SenateSource


class SenateSourceTestCase(TestCase):
    def test_correct_senate_data_extraction(self):
        senate_seats = SenateSource().get_resource(SenateHistory())
        self.assertGreater(len(senate_seats), 0)
