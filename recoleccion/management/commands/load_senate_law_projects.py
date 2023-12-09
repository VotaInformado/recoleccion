from tqdm import tqdm
import logging
import time

# Project
from recoleccion.utils.custom_command import YearThreadedCommand
from recoleccion.components.data_sources.law_projects_source import (
    SenateLawProjectsSource,
)
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter


class Command(YearThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"
    denomination = "load_senate_law_projects"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--starting-year", type=int, default=2023)

    def main_function(self, starting_year: int, step_size: int):
        source = SenateLawProjectsSource(threading=True)
        year = starting_year
        while True:
            data = source.get_data(year)
            if data.empty:
                self.save_missing_record(year)
            LawProjectsWriter.write(data)
            year = year - step_size
            if year < 1983:
                return  # Si pasás un año menor a 1983, en lugar de tirar un error, te da todos los proyectos de ley

    def missing_only_function(self, starting_index: int, step_size: int):
        source = SenateLawProjectsSource(threading=True)
        missing_years = self.get_missing_records()
        for index in tqdm(range(starting_index, len(missing_years), step_size)):
            year = missing_years[index].record_value
            attempts = 0
            while attempts < 15:
                data = source.get_data(year)
                if not data.empty:
                    self.logger.info(f"Data for year {year} was found!")
                    self.delete_missing_record(year)
                    break
                attempts += 1
                self.logger.warning(f"Empty data for year {year}. Attempt {attempts}")
                time.sleep(3)
            if data.empty:  # the max attempts were reached and no data
                self.logger.error(f"(Missing only) Empty data for year {year}. Max attempts reached")
                self.save_missing_record(year)
                continue
            LawProjectsWriter.write(data)
