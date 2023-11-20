import threading

# Base command


# Django
from django.db import transaction

# Components
from recoleccion.utils.custom_command import CustomCommand
from recoleccion.components.data_sources.authors_source import SenateAuthorsSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.authors_writer import AuthorsWriter
import logging

logger = logging.getLogger(__name__)


class Command(CustomCommand):
    help = "Load laws from the deputy source"

    def __init__(self):
        super().__init__()
        self.reverse_index = True

    def add_arguments(self, parser):
        parser.add_argument("starting_year", type=int, default=2023)

    def main_function(self, starting_year: int, step_size: int):
        year = starting_year
        source = SenateAuthorsSource(threading=True)
        while True:
            data = source.get_data(year)
            linker = PersonLinker()
            linked_data = linker.link_persons(data)
            AuthorsWriter.write(linked_data)
            year = year - step_size
            if year < 1983:
                return  # Si pasás un año menor a 1983, en lugar de tirar un error, te da todos los proyectos de ley
