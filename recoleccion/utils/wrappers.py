from unittest.mock import PropertyMock
from functools import wraps
import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

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


def manual_pagination(func):
    def wrapper(view, request, *args, **kwargs):
        response: Response = func(view, request, *args, **kwargs)
        page = request.query_params.get("page", None)
        page_size = request.query_params.get("page_size", None)
        if not page or not page_size:
            return response

        queryset = response.data
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        paged_queryset = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(paged_queryset)
    return wrapper
