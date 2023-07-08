from django.test import TestCase

from recoleccion.components.data_sources import DeputySource
from recoleccion.components.data_sources.deputy_source import DeputyHistory
from recoleccion.components.data_sources.senate_source import SenateHistory, SenateSource

class DeputySourceTestCase(TestCase):

    def test_correct_data_extraction(self):
        deputy_seats = DeputySource().get_resource(DeputyHistory())
        self.assertGreater(len(deputy_seats), 0)
