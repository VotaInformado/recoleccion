import threading
from tqdm import tqdm

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.authors_source import DeputiesAuthorsSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.authors_writer import AuthorsWriter
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)

    def handle(self, *args, **options):
        self.source = DeputiesAuthorsSource()
        total_pages = self.source.get_total_pages()
        options["total_pages"] = total_pages
        super().handle(*args, **options)

    def main_function(self, starting_page: int, total_pages: int, step_size: int):
        for page in tqdm(range(starting_page, total_pages + 1, step_size)):
            attempts = 0
            while attempts < 5:
                data = self.source.get_data(page)
                if data.empty:
                    break
                attempts += 1
                self.logger.warning(f"Empty data for page {page}. Attempt {attempts}")
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)
