import pandas as pd

# Components
from recoleccion.exceptions.custom import PageNotFound
from recoleccion.utils.custom_command import PeriodThreadedCommand
from recoleccion.components.data_sources.day_orders_source import DeputiesDayOrderSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(PeriodThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"
    denomination = "load_deputies_day_orders"

    def add_arguments(self, parser):
        parser.add_argument("--starting-period", type=int, default=0)

    def main_function(self, starting_period: int, step_size: int):
        i = starting_period
        while True:
            data = self._fetch_data(i)
            if data is None:  # Page not found, indicating that there are no more pages
                break
            elif data.empty:  # Empty data, indicating that the page is missing
                self.save_missing_record(i)
            else:
                LawProjectsWriter.update_day_orders(data)
            i += step_size

    def _fetch_data(self, period: int):
        attempts = 0
        while attempts < 5:
            try:
                data: pd.DataFrame = DeputiesDayOrderSource.get_data(period=period)
                if data.empty:
                    self.logger.warning(f"Empty data for period {period} (attempt {attempts})")
                    attempts += 1
                else:
                    return data
            except PageNotFound:
                return None
