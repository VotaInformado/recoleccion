import pandas as pd

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.day_orders_source import DeputiesDayOrderSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.utils.custom_logger import CustomLogger


class Command(BaseCommand):
    logger = CustomLogger()
    help = "Load laws from the deputy source"

    def add_arguments(self, parser):
        parser.add_argument("--starting-period", type=int, default=0)

    def handle(self, *args, **options):
        starting_period = options["starting_period"]
        i = starting_period
        while True:
            data: pd.DataFrame = DeputiesDayOrderSource.get_data(period=i)
            i += 1
            if data.empty:
                break
            LawProjectsWriter.update_day_orders(data)
