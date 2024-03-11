import pandas as pd
from unittest.mock import patch
from django.conf import settings
import logging

# Project
from recoleccion.components.linkers import Linker
from recoleccion.models.person import Person


logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


class FakeClass:
    def fake_method(self):
        pass


class FakeResponse:
    def __init__(self, content: dict, status_code=200):
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content


def is_internal_mock_enabled():
    return getattr(settings, "INTERNAL_MOCK_ENABLED", True)


def mock_method(mocked_class, method_name, return_value=None, new_callable=None):
    """Mocks a method of a class"""
    patcher = patch.object(mocked_class, method_name, return_value=return_value, new_callable=new_callable)
    return patcher


def mock_method_side_effect(mocked_class, method_name, side_effect, autospec=True):
    """Mocks a method of a class"""
    # Does not deppend on internal_mock_enabled, since we'll always want the side effects to happen
    patcher = patch.object(mocked_class, method_name, side_effect=side_effect, autospec=autospec)
    return patcher


def mock_class_attribute(mocked_class, attribute_name, new_attribute_value):
    """Mocks an attribute of a class"""
    mocked_class_name = mocked_class.__name__
    if is_internal_mock_enabled():
        patcher = patch.object(mocked_class, attribute_name, new=new_attribute_value)
        return patcher
    else:
        # This function needs to return a context manager, so this must be used
        patcher = patch.object(FakeClass, "fake_method", return_value=new_attribute_value)
        return patcher


def mock_data_source_json(src_file):
    """Mocks a data source json file"""
    base_dir = "recoleccion/tests/test_helpers/files/"
    file_dir = base_dir + src_file
    return pd.read_json(file_dir)


def mock_data_source_csv(src_file):
    """Mocks a data source json file"""
    base_dir = "recoleccion/tests/test_helpers/files/"
    file_dir = base_dir + src_file
    return pd.read_csv(file_dir)


def get_file_data_length(src_file):
    if ".json" in src_file:
        data = mock_data_source_json(src_file)
    else:
        data = mock_data_source_csv(src_file)
    return len(data)


def confidence(match):
    return match[1][0][1] if len(match[1]) > 0 else -1


def tuple_of_tuples_to_list_of_lists(data):
    if isinstance(data, tuple):
        return [tuple_of_tuples_to_list_of_lists(item) for item in data]
    else:
        return data


def list_of_lists_to_tuple_of_tuples(data):
    if isinstance(data, list):
        return tuple(list_of_lists_to_tuple_of_tuples(item) for item in data)
    else:
        return data


def mock_linking_results(instance, *args, **kwargs):
    logger.debug("Mocking linking results...")
    real_results = settings.REAL_METHOD(instance, *args, **kwargs)
    logger.debug(f"Messy indexes: {settings.MESSY_INDEXES}")
    logger.debug(f"Canonical indexes: {settings.CANONICAL_INDEXES}")
    logger.debug(f"Initial results: {real_results}")
    max_conf_pair = max(real_results, key=lambda x: confidence(x))
    max_confidence = max_conf_pair[1][0][1] if max_conf_pair[1] else 0
    dubious_lower_limit = max_confidence * Linker.DUBIOUS_LOWER_LIMIT
    dubious_lower_limit = max(dubious_lower_limit, Linker.MIN_ACCEPTABLE_LOWER_LIMIT)
    dubious_upper_limit = max_confidence * Linker.DUBIOUS_UPPER_LIMIT
    dubious_upper_limit = max(dubious_upper_limit, Linker.MIN_ACCEPTABLE_UPPER_LIMIT)
    dubious_score = (dubious_lower_limit + dubious_upper_limit) / 2
    canonical_pointer = 0
    for i, original_result in enumerate(real_results):
        messy_index = original_result[0]
        if messy_index not in settings.MESSY_INDEXES:
            continue
        # we change only the score of the index that we want to be dubious
        new_list = tuple_of_tuples_to_list_of_lists(original_result)
        if not new_list[1]:
            new_list[1].append([0, 0])
        canonical_index = settings.CANONICAL_INDEXES[canonical_pointer]
        new_list[1][0][0] = canonical_index
        canonical_pointer += 1
        new_list[1][0][1] = dubious_score
        real_results[i] = list_of_lists_to_tuple_of_tuples(new_list)
    logger.debug(f"Final results: {real_results}")
    return real_results


def mock_load_exact_matches(instance, messy_data):
    return pd.DataFrame(), messy_data


def mock_legislator_response(legislator_id):
    response_data = {
        "legislator": legislator_id,
        "vote": "Aprobado",
    }
    return FakeResponse(content=response_data)


def mock_chamber_response():
    legislator_ids = Person.objects.filter(last_seat__isnull=False).values_list("id", flat=True)
    response_data = []
    for i in range(10):
        response_data.append(
            {
                "legislator": legislator_ids[i],
                "vote": "Aprobado",
            }
        )
    return FakeResponse(content=response_data)
