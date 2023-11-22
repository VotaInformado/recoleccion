import argparse
import inspect
import threading
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

    def handle(self, *args, **options):
        threads = []
        if options.get("only_missing"):
            target_function = self.missing_only_function
        else:
            target_function = self.main_function
        function_params = self.get_function_params(target_function, options)
        for index in range(self.THREAD_AMOUNT):
            if options.get("only_missing"):
                function_params["starting_index"] = index
            else:
                index_name = self.index_name  # starting_page, starting_period or starting_year
                function_params[index_name] = index
            function_params["step_size"] = self.THREAD_AMOUNT
            thread = threading.Thread(name=f"Thread {index+1}", target=target_function, kwargs=function_params)
            threads.append(thread)
            self.logger.info(f"Starting thread {index+1}")
            thread.start()
            if self.reverse_index:
                index -= 1
            else:
                index += 1

        for thread in threads:
            thread.join()

    def main_function(self):
        raise NotImplementedError

    def missing_only_function(self):
        raise NotImplementedError


class YearThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = True
        self.index_name = "starting_year"


class PageThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_page"


class PeriodThreadedCommand(CustomCommand):
    def __init__(self):
        super().__init__()
        self.reverse_index = False
        self.index_name = "starting_period"
