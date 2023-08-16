# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import DeputyLawProjectsSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.utils.custom_logger import CustomLogger


class Command(BaseCommand):
    logger = CustomLogger()
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)
        parser.add_argument("--ending-page", type=int, default=None)

    def data_not_retrieved(self, data, added):
        # no puedo comparar a -1, -1 porque cuando data es un DF rompe
        return type(data) == int and type(added) == int

    def handle(self, *args, **options):
        starting_page = options["starting_page"]
        ending_page = options["ending_page"] or float("inf")
        i = starting_page
        step_size = 1
        first_time = True
        while True:
            data, added = DeputyLawProjectsSource.get_data(i, first_time, step_size)
            if self.data_not_retrieved(data, added):
                continue
            first_time = False
            i += step_size
            if not added or i >= ending_page:
                break
            LawProjectsWriter.write(data)
