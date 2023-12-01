import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.components.data_sources.law_projects_source import LawProjectsStatusSource

# Utils


class Command(BaseCommand):
    def handle(self, *args, **options):
        source = LawProjectsStatusSource()
        status_data = source.get_data()
        LawProjectsWriter.update_projects_status(status_data)
