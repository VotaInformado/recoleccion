import pandas as pd

# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources.votes_source import DeputyVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.components.linkers import PersonLinker


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def handle(self, *args, **options):
        year = options["starting_year"]
        writer = VotesWriter()
        while year >= 1990:
            votes: pd.DataFrame = DeputyVotesSource.get_data(year)
            if votes.empty:
                return
            linker = PersonLinker()
            linked_data = linker.link_persons(votes)
            writer.write(linked_data)
            year -= 1
