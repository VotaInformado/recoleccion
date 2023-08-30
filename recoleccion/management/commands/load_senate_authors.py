import threading

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.authors_source import SenateAuthorsSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.authors_writer import AuthorsWriter
from recoleccion.utils.custom_logger import CustomLogger


class Command(BaseCommand):
    logger = CustomLogger(threading=True)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def handle(self, *args, **options):
        self.THREAD_AMOUNT = 8
        year = options["starting_year"]
        threads = []
        for i in range(self.THREAD_AMOUNT):
            thread = threading.Thread(name=f"Thread {i+1}", target=self.main_function, args=(year, self.THREAD_AMOUNT))
            threads.append(thread)
            thread.start()
            year -= 1

        for thread in threads:
            thread.join()

    def main_function(self, year: int, step_size: int):
        source = SenateAuthorsSource(threading=True)
        while True:
            data = source.get_data(year)
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)
            year = year - step_size
            if year < 1983:
                return  # Si pasás un año menor a 1983, en lugar de tirar un error, te da todos los proyectos de ley
