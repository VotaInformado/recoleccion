import threading

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.authors_source import DeputiesAuthorsSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.authors_writer import AuthorsWriter
from recoleccion.utils.custom_logger import CustomLogger


class Command(BaseCommand):
    logger = CustomLogger(threading=True)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-page", type=int, default=1)

    def handle(self, *args, **options):
        self.THREAD_AMOUNT = 8
        page = options["starting_page"]
        threads = []
        for i in range(self.THREAD_AMOUNT):
            thread = threading.Thread(
                name=f"Thread {i+1}",
                target=self.main_function,
                args=(page, self.THREAD_AMOUNT),
            )
            threads.append(thread)
            thread.start()
            page += 1

        for thread in threads:
            thread.join()

    def main_function(self, page: int, step_size: int):
        source = DeputiesAuthorsSource()
        while True:
            attempts = 0
            while attempts < 5:
                data = source.get_data(page)
                if data.empty:
                    break
                attempts += 1
                self.logger.warning(f"Empty data for page {page}. Attempt {attempts}")
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)
            page += step_size
