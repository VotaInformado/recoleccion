# Base command
from django.core.management.base import BaseCommand
from django.db import transaction

# Dates
from datetime import datetime as dt

# Components
from recoleccion.components.writers.laws_writer import LawsWriter
from recoleccion.components.data_sources.laws_source import LawSource


class Command(BaseCommand):
    help = "Load laws from the deputy source"

    @transaction.atomic
    def handle(self, *args, **options):
        laws_data = LawSource.get_data()
        writer = LawsWriter()
        written_laws = writer.write(laws_data)
        
