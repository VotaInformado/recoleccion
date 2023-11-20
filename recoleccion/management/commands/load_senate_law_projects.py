# Components
from recoleccion.utils.custom_command import YearThreadedCommand
from recoleccion.components.data_sources.law_projects_source import (
    SenateLawProjectsSource,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(YearThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def main_function(self, starting_year: int, step_size: int):
        source = SenateLawProjectsSource(threading=True)
        year = starting_year
        while True:
            data = source.get_data(year)
            LawProjectsWriter.write(data)
            year = year - step_size
            if year < 1983:
                return  # Si pasás un año menor a 1983, en lugar de tirar un error, te da todos los proyectos de ley
