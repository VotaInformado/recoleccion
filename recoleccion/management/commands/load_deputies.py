# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources import CurrentDeputies, DeputySource
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.persons_writer import PersonsWriter
from recoleccion.components.writers.deputies_writer import DeputiesWriter


class Command(BaseCommand):
    DIPUTIES_CAPACITY = 257

    def handle(self, *args, **options):
        print("Start getting deputies at: ", dt.now())
        deputies_data = DeputySource().get_resource(CurrentDeputies())
        persons_writer = PersonsWriter()  # TODO: make these class methods
        written_persons = persons_writer.write(deputies_data)
        linker = PersonLinker()
        linked_data = linker.link_persons(deputies_data)
        deputies_writer = DeputiesWriter()
        written_deputies = deputies_writer.write(linked_data)
        assert len(written_persons) == self.DIPUTIES_CAPACITY
        assert len(written_deputies) == self.DIPUTIES_CAPACITY
