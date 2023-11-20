import pandas as pd

# Components
from recoleccion.utils.custom_command import PeriodThreadedCommand
from recoleccion.components.data_sources.day_orders_source import DeputiesDayOrderSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
import logging


class Command(PeriodThreadedCommand):
    logger = logging.getLogger(__name__)
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-period", type=int, default=0)

    def main_function(self, starting_period: int, step_size: int):
        i = starting_period
        while True:
            data: pd.DataFrame = DeputiesDayOrderSource.get_data(period=i)
            if data.empty:
                break
            LawProjectsWriter.update_day_orders(data)
            i += step_size
