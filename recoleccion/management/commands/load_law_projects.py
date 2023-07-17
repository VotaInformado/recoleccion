# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt

# Components
from recoleccion.components.writers.laws_writer import LawsWriter
from recoleccion.components.data_sources.laws_source import LawSource

class Command(BaseCommand):
    help = "Load laws from the deputy source"
    
    def handle(self, *args, **options):
        laws_data = LawSource.get_data()
        print("Start getting senators at: ", dt.now())
        writer = LawsWriter()
        written_laws = writer.write(laws_data)
        print(f"Finished writing {len(written_laws)} laws")
