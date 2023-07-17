# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources import CurrentSenate
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.persons_writer import PersonsWriter
from recoleccion.components.writers.senators_writer import SenatorsWriter


class Command(BaseCommand):
    SENATE_CAPACITY = 72

    def handle(self, *args, **options):
        senators_data = CurrentSenate.get_data()
        persons_writer = PersonsWriter()
        written_persons = persons_writer.write(senators_data, add_social_data=True)
        linker = PersonLinker()
        linked_data = linker.link_persons(senators_data)
        senators_writer = SenatorsWriter()
        written_senators = senators_writer.write(linked_data)
        assert len(written_persons) == self.SENATE_CAPACITY
        assert len(written_senators) == self.SENATE_CAPACITY
        # TODO: probablemente, se necesite un refactor
