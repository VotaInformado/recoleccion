from unittest.mock import PropertyMock

# Project
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.components.linkers.linker import Linker


def linking_test(original_function):
    TEST_LINKER_FILE_PATH = "recoleccion/components/linkers/training/tests"

    def inner_function(*args, **kwargs):
        with mck.mock_method(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
            attr_mock.return_value = TEST_LINKER_FILE_PATH
            return original_function(*args, **kwargs)

    return inner_function
