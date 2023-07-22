# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources import CurrentSenate
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.senators_writer import SenatorsWriter
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class Command(BaseCommand):
    SENATE_CAPACITY = 72

    def handle(self, *args, **options):
        senators_data = CurrentSenate.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(senators_data)
        written_senators = SenatorsWriter.write(linked_data)
        active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR)
        assert len(active_senators) == self.SENATE_CAPACITY
        # TODO: probablemente se necesite un refactor
