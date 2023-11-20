import threading
import time
from tqdm import tqdm

# Base command
from recoleccion.utils.custom_command import PageThreadedCommand
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.components.data_sources.law_projects_source import DeputyLawProjectsSource
import logging


class Command(PageThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)

    def handle(self, *args, **options):
        total_pages = DeputyLawProjectsSource.get_total_pages()
        if not options.get("only_missing"):
            options["total_pages"] = total_pages
        super().handle(*args, **options)

    def main_function(self, starting_page: int, total_pages: int, step_size: int):
        source = DeputyLawProjectsSource()
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
            LawProjectsWriter.write(data)

    def missing_only_function(self, starting_page: int, total_pages: int, step_size: int):
        source = DeputyLawProjectsSource()
        missing_pages = self.get_missing_records()
        for index in tqdm(range(0, len(missing_pages), step_size)):
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
                self.save_missing_record(page)
                continue
            LawProjectsWriter.write(data)
