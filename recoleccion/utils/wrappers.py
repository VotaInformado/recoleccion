import logging
from functools import wraps
from unittest.mock import PropertyMock

# Project
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.components.linkers.linker import Linker

logger = logging.getLogger(__name__)


def linking_test(original_function):
    TEST_LINKER_FILE_PATH = "recoleccion/components/linkers/training/tests"

    def inner_function(*args, **kwargs):
        with mck.mock_method(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
            attr_mock.return_value = TEST_LINKER_FILE_PATH
            return original_function(*args, **kwargs)

    return inner_function


def allowed_to_fail(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Test '{func.__name__}' failed but will be ignored: {e}")

    return wrapper
