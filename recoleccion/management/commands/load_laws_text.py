# Base command
import pandas as pd
import logging

# Project
from recoleccion.components.writers.laws_writer import LawsWriter
from recoleccion.components.data_sources.laws_source import GovernmentLawSource
from recoleccion.utils.custom_command import PageThreadedCommand

logger = logging.getLogger(__name__)


class Command(PageThreadedCommand):
    LAST_PAGE = 200
    denomination = "load_laws_text"
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--starting-page", type=int, default=1)

    def main_function(self, starting_page: int, step_size: int):
        writer = LawsWriter()
        page = starting_page
        while page <= self.LAST_PAGE:
            logger.info(f"Getting page {page}")
            laws: pd.DataFrame = GovernmentLawSource.get_page_data(page)
            if laws.empty:
                self.save_missing_record(page)
            writer.write(laws)
            page += step_size
