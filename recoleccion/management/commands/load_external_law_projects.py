# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import ExternalLawProjectsSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)
        parser.add_argument("--ending-page", type=int, default=None)

    def handle(self, *args, **options):
        starting_page = options["--starting-page"]
        ending_page = options["ending_page"] or float("inf")
        i = starting_page
        step_size = 10
        while True:
            data, added = ExternalLawProjectsSource.get_data(starting_page=i, step_size=step_size)
            i += step_size
            if not added or i >= ending_page:
                break
            LawProjectsWriter.write(data)


# TODO: Delete?
