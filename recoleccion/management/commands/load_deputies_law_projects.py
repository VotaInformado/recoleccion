import threading
import time
from tqdm import tqdm

# Base command
from recoleccion.utils.custom_command import CustomCommand
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.components.data_sources.law_projects_source import DeputyLawProjectsSource
import logging


class Command(CustomCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("starting_page", type=int, default=1)

    def handle(self, *args, **options):
        self.source = DeputyLawProjectsSource()
        options["total_pages"] = self.source.get_total_pages()
        super().handle(*args, **options)

    def main_function(self, starting_page: int, total_pages: int, step_size: int):
        for page in tqdm(range(starting_page, total_pages + 1, step_size)):
            attempts = 0
            while attempts < 5:
                data = self.source.get_data(page)
                if not data.empty:
                    break
                attempts += 1
                self.logger.warning(f"Empty data for page {page}. Attempt {attempts}")
                time.sleep(1)
            if attempts == 5:
                self.logger.error(f"Empty data for page {page}. Skipping.")
                continue
            LawProjectsWriter.write(data)
