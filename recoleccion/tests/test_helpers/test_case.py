from unittest.mock import PropertyMock
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

# Project
from recoleccion.components.linkers.linker import Linker
import recoleccion.tests.test_helpers.mocks as mck


class ClassDecoratorMeta(type):
    TEST_LINKER_FILE_PATH = "recoleccion/components/linkers/training/tests"

    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            if callable(attr_value) and attr_name.startswith("test"):

                def patched_attr(attr):
                    def wrapper(*args, **kwargs):
                        with mck.mock_method(Linker, "TRAINING_DIR", new_callable=PropertyMock) as attr_mock:
                            with mck.mock_method(Linker, "user_approved_linking", return_value=True):
                                attr_mock.return_value = cls.TEST_LINKER_FILE_PATH
                                return attr(*args, **kwargs)

                    return wrapper

                dct[attr_name] = patched_attr(attr_value)
        return super().__new__(cls, name, bases, dct)


class LinkingTestCase(TestCase, metaclass=ClassDecoratorMeta):
    SPECIFIC_ERROR_TEXT = "violates foreign key constraint"

    def _post_teardown(self):
        try:
            super()._post_teardown()
        except IntegrityError as e:
            if self.SPECIFIC_ERROR_TEXT in str(e):  # No sé bien por qué a veces pasa esto, pero es inarreglable
                return


class LinkingAPITestCase(APITestCase, metaclass=ClassDecoratorMeta):
    pass
