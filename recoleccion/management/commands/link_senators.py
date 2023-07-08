# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources.senate_source import SenateHistory, SenateSource
from recoleccion.components.linkers import PersonLinker



class Command(BaseCommand):
    """
    Command for creating monthly fees report
    """

    # def add_arguments(self, parser):
    #     parser.add_argument("-month", type=int)
    #     parser.add_argument("-year", type=int)

    def handle(self, *args, **options):
        from recoleccion.components.writers.senators_writer import SenatorsWriter
        print("Start getting senate at: ", dt.now())
        cargos_senadores = SenateSource().get_resource(SenateHistory())
        
        print("Start linking senate at: ", dt.now())
        linker = PersonLinker()
        linked_data = linker.link_persons(cargos_senadores)

        print("Start writing senate at: ", dt.now())
        writer = SenatorsWriter()
        writer.write(linked_data)
        print("End writing senate at: ", dt.now())
