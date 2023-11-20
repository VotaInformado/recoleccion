import threading
import time
from tqdm import tqdm

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import (
    DeputyLawProjectsSource,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)

    def handle(self, *args, **options):
        self.THREAD_AMOUNT = 8
        page = options["starting_page"]
        threads = []
        self.source = DeputyLawProjectsSource()
        total_pages = self.source.get_total_pages()
        for i in range(self.THREAD_AMOUNT):
            thread = threading.Thread(
                name=f"Thread {i+1}",
                target=self.main_function,
                args=(page, total_pages, self.THREAD_AMOUNT),
            )
            threads.append(thread)
            thread.start()
            page += 1

        for thread in threads:
            thread.join()

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
