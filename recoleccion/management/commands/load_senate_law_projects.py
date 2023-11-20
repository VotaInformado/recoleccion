import threading

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import (
    SenateLawProjectsSource,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def handle(self, *args, **options):
        self.THREAD_AMOUNT = 8
        year = options["starting_year"]
        threads = []
        self.logger.info(
            "STARTING COMMAND: load_senate_law_projects"
            + f" with {self.THREAD_AMOUNT} threads"
            + f" and starting year {year}"
        )
        for i in range(self.THREAD_AMOUNT):
            thread = threading.Thread(
                name=f"Thread {i+1}",
                target=self.main_function,
                args=(year, self.THREAD_AMOUNT),
            )
            threads.append(thread)
            thread.start()
            year -= 1

        for thread in threads:
            thread.join()
        self.logger.info("FINISHED COMMAND: load_senate_law_projects")

    def main_function(self, year: int, step_size: int):
        source = SenateLawProjectsSource(threading=True)
        while True:
            data = source.get_data(year)
            LawProjectsWriter.write(data)
            year = year - step_size
            if year < 1983:
                return  # Si pasás un año menor a 1983, en lugar de tirar un error, te da todos los proyectos de ley
