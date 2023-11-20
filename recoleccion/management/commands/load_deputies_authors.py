import time
from tqdm import tqdm

# Base command
# Django
from django.db import transaction

# Components
from recoleccion.utils.custom_command import PageThreadedCommand
from recoleccion.components.data_sources.authors_source import DeputiesAuthorsSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.authors_writer import AuthorsWriter
import logging


class Command(PageThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)

    def handle(self, *args, **options):
        total_pages = DeputiesAuthorsSource.get_total_pages()
        if not options.get("only_missing"):
            options["total_pages"] = total_pages
        super().handle(*args, **options)

    def main_function(self, starting_page: int, total_pages: int, step_size: int):
        source = DeputiesAuthorsSource()
        for page in tqdm(range(starting_page, total_pages + 1, step_size)):
            attempts = 0
            while attempts < 5:
                data = source.get_data(page)
                if not data.empty:
                    break
                attempts += 1
                self.logger.warning(f"Empty data for page {page}. Attempt {attempts}")
                time.sleep(1)
            if data.empty:  # the max attempts were reached and no data
                self.logger.error(f"Empty data for page {page}. Max attempts reached")
                self.save_missing_record(page)
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)

    def missing_only_function(self, step_size: int):
        source = DeputiesAuthorsSource()
        missing_pages = self.get_missing_records()
        for index in tqdm(0, len(missing_pages), step_size):
            page = missing_pages[index].record_value
            attempts = 0
            while attempts < 10:
                data = source.get_data(page)
                if not data.empty:
                    self.logger.info(f"Data for page {page} was found!")
                    self.delete_missing_record(page)
                    break
                attempts += 1
                self.logger.warning(f"Empty data for page {page}. Attempt {attempts}")
                time.sleep(1)
            if data.empty:  # the max attempts were reached and no data
                self.logger.error(f"(Missing only) Empty data for page {page}. Max attempts reached")
                continue
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)
