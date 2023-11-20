import argparse
from django.core.management.base import BaseCommand, CommandParser
import threading

# Project
from recoleccion.models.missing_record import MissingRecord


class CustomCommand(BaseCommand):
    THREAD_AMOUNT = 8
    index_name = None

    class Meta:
        abstract = True

    def delete_missing_record(self, record_value: int):
        MissingRecord.objects.filter(class_name=self.__class__.__name__, record_value=record_value).delete()

    def save_missing_record(self, record_value: int):
        MissingRecord.objects.create(class_name=self.__class__.__name__, record_value=record_value)

    def get_missing_records(self):
        return MissingRecord.objects.filter(class_name=self.__class__.__name__)

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--only-missing", action=argparse.BooleanOptionalAction, default=False)

    def handle(self, *args, **options):
        threads = []
        if options["only_missing"]:
            target_function = self.missing_only_function
        else:
            target_function = self.main_function
        for index in range(self.THREAD_AMOUNT):
            if not options["only_missing"]:
                index_name = self.index_name  # starting_page, starting_period or starting_year
                options[index_name] = index
            options["step_size"] = self.THREAD_AMOUNT
            thread = threading.Thread(name=f"Thread {index+1}", target=target_function, kwargs=options)
            threads.append(thread)
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
