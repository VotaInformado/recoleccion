from django.test import TestCase
from django.core.management import call_command

# Unitest
from unittest.mock import patch, PropertyMock

from recoleccion.components.data_sources import DeputySource
from recoleccion.components.data_sources.deputy_source import DeputyHistory
from recoleccion.components.data_sources.senate_source import SenateHistory, SenateSource
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.linkers.linker import Linker
from recoleccion.tests.test_helpers.faker import create_fake_df


class CommandTestCase(TestCase):
    def test_correct_sentors_linking(self):
        columns = {
            "name": "str",
            "last_name": "str",
            "id": "int",
            "province": "str",
            "start_of_term": "date",
            "end_of_term": "date",
        }
        canonical_data: dict = create_fake_df(columns, n=10)
        messy_data: dict = create_fake_df(columns, n=8)
        with patch.object(PersonLinker, "get_messy_data", return_value=messy_data):
            with patch.object(PersonLinker, "get_canonical_data", return_value=canonical_data):
                with patch.object(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
                    attr_mock.return_value = "recoleccion/components/linkers/training/tests"
                    call_command("link_senators")
        self.assertTrue(True)
