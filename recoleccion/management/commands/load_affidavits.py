import pandas as pd
import logging

# Base command

# Project
from recoleccion.utils.custom_command import YearThreadedCommand
from recoleccion.components.data_sources.affidavits_source import AffidavitsSource
from recoleccion.components.writers.affidavits_writer import AffidavitsWriter
from recoleccion.components.linkers import PersonLinker

logger = logging.getLogger(__name__)


class Command(YearThreadedCommand):
    denomination = "load_deputies_votes"

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2020)

    def handle(self, *args, **options):
        AffidavitsSource.load_data()  # loads the zip file content into the class just once
        super().handle(*args, **options)

    def main_function(self, starting_year: int, step_size: int):
        year = starting_year
        while True:
            data: pd.DataFrame = AffidavitsSource.get_data(year)
            if data.empty:
                logger.info(f"No data found for year {year}, stopping")
                break
            linker = PersonLinker(use_alternative_names=True)
            # we have to skip manual linking, the messy data is just too large
            linked_data = linker.link_persons(data)
            AffidavitsWriter.write(linked_data)
            year += step_size
