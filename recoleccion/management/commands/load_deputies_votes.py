import pandas as pd

# Base command

# Project
from recoleccion.utils.custom_command import YearThreadedCommand
from recoleccion.components.data_sources.votes_source import DeputyVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.components.linkers import PersonLinker


class Command(YearThreadedCommand):
    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def write_year_votes(self, starting_year: int, step_size: int):
        writer = VotesWriter()
        year = starting_year
        while year >= 1990:
            votes: pd.DataFrame = DeputyVotesSource.get_data(year)
            if votes.empty:
                return
            linker = PersonLinker()
            linked_data = linker.link_persons(votes)
            writer.write(linked_data)
            year -= step_size
