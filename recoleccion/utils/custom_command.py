from django.conf import settings
import argparse
import inspect
import threading  # TODO: ver si también se pueden usar procesos
import logging

# Project
from django.core.management.base import BaseCommand, CommandParser
from recoleccion.models.missing_record import MissingRecord


class CustomCommand(BaseCommand):
    logger = logging.getLogger(__name__)
    THREAD_AMOUNT = 8
    index_name = None
    denomination = None

    class Meta:
        abstract = True

    def delete_missing_record(self, record_value: int):
        MissingRecord.objects.filter(class_name=self.denomination, record_value=record_value).delete()

    def save_missing_record(self, record_value: int):
        existing_record = MissingRecord.objects.filter(class_name=self.denomination, record_value=record_value).first()
        if existing_record:
            return
        MissingRecord.objects.create(class_name=self.denomination, record_value=record_value)

    def get_missing_records(self):
        return MissingRecord.objects.filter(class_name=self.denomination)

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--only-missing", action=argparse.BooleanOptionalAction)

    def get_function_params(self, target_function, options: dict):
        target_function_params = inspect.signature(target_function).parameters
        function_params = {}
        for param_name, param in target_function_params.items():
            if param_name in options:
                function_params[param_name] = options[param_name]
        return function_params

    def get_current_index(self, *args, **options):
        raise NotImplementedError

    def handle(self, *args, **options):
        threads = []
        if options.get("only_missing"):
            self.target_function = self.missing_only_function
        else:
            self.target_function = self.main_function
        function_params = self.get_function_params(self.target_function, options)
        if settings.USE_THREADS:
            self.handle_threaded(function_params, options)
        else:
            self.handle_unthreaded(function_params, options)

    def handle_threaded(self, function_params: dict, options: dict):
        threads = []
        for index in range(self.THREAD_AMOUNT):
            if options.get("only_missing"):
                function_params["starting_index"] = index
            else:
                index_name = self.index_name  # starting_page, starting_period or starting_year
                pagination_index = self.get_current_index(loop_index=index, options=options)
                function_params[index_name] = pagination_index
            function_params["step_size"] = self.THREAD_AMOUNT
            thread = threading.Thread(name=f"Thread {index+1}", target=self.target_function, kwargs=function_params)
            threads.append(thread)
            self.logger.info(f"Starting thread {index+1}")
            thread.start()
            if self.reverse_index:
                index -= 1
            else:
                index += 1

        for thread in threads:
            thread.join()

    def handle_unthreaded(self, function_params: dict, options: dict):
        INDEX = self.get_current_index(0, options)
        STEP_SIZE = 1
        if options.get("only_missing"):
            function_params["starting_index"] = INDEX
        else:
            index_name = self.index_name
            function_params[index_name] = INDEX
        function_params["step_size"] = STEP_SIZE
        self.target_function(**function_params)

    def main_function(self):
        raise NotImplementedError

    def missing_only_function(self):
        raise NotImplementedError


class YearThreadedCommand(CustomCommand):
    def get_current_index(self, loop_index, options):
        starting_year = options.get("starting_year")
        actual_index = starting_year - loop_index
        return actual_index

    def __init__(self):
        super().__init__()
        self.reverse_index = True
        self.index_name = "starting_year"


class PageThreadedCommand(CustomCommand):
    def get_current_index(self, loop_index, _):
        return loop_index

    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_page"


class PeriodThreadedCommand(CustomCommand):
    def get_current_index(self, loop_index, _):
        return loop_index

    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_period"
