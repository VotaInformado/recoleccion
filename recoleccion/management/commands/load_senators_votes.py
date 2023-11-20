import pandas as pd
import threading

# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources.votes_source import SenateVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.components.linkers import PersonLinker
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    def handle(self, *args, **options):
        THREAD_AMOUNT = 6
        year = options["starting_year"]
        threads = []
        for _ in range(THREAD_AMOUNT):
            thread = threading.Thread(target=self.write_year_votes, args=(year, THREAD_AMOUNT))
            threads.append(thread)
            thread.start()
            year -= 1

        for thread in threads:
            thread.join()

    def write_year_votes(self, year: int, step_size: int):
        self.logger.info(f"Writing votes for year {year}...")
        writer = VotesWriter()
        while year >= 1990:
            votes: pd.DataFrame = SenateVotesSource.get_data(year)
            if votes.empty:
                return
            linker = PersonLinker()
            linked_data = linker.link_persons(votes)
            writer.write(linked_data)
            self.logger.info(f"Written votes for year {year}")
            year -= step_size
