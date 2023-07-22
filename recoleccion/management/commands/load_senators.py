# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources import CurrentSenate
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.senators_writer import SenatorsWriter
from recoleccion.models.senate_seat import SenateSeat


class Command(BaseCommand):
    SENATE_CAPACITY = 72

    def handle(self, *args, **options):
        senators_data = CurrentSenate.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(senators_data)
        written_senators = SenatorsWriter.write(linked_data)
        active_senators = SenateSeat.objects.filter(is_active=True)
        assert len(active_senators) == self.SENATE_CAPACITY
        # TODO: probablemente se necesite un refactor
