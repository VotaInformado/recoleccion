# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources.senate_source import SenateHistory
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.senators_writer import SenatorsWriter


class Command(BaseCommand):
    """
    Command for creating monthly fees report
    """

    # def add_arguments(self, parser):
    #     parser.add_argument("-month", type=int)
    #     parser.add_argument("-year", type=int)

    def handle(self, *args, **options):
        senate_seats_data = SenateHistory.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(senate_seats_data)
        writer = SenatorsWriter()
        writer.write(linked_data)
