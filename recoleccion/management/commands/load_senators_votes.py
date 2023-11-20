import pandas as pd

# Project
from recoleccion.utils.custom_command import YearThreadedCommand
from recoleccion.components.data_sources.votes_source import SenateVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.components.linkers import PersonLinker
import logging


class Command(YearThreadedCommand):
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def write_year_votes(self, starting_year: int, step_size: int):
        self.logger.info(f"Writing votes for year {starting_year}...")
        writer = VotesWriter()
        year = starting_year
        while year >= 1990:
            votes: pd.DataFrame = SenateVotesSource.get_data(year)
            if votes.empty:
                return
            linker = PersonLinker()
            linked_data = linker.link_persons(votes)
            writer.write(linked_data)
            self.logger.info(f"Written votes for year {year}")
            year -= step_size
