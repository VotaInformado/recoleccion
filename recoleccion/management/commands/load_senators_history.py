# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources import SenateHistory
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.senators_writer import SenatorsWriter
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeats

# Exceptions
from recoleccion.exceptions.custom import SenateLoadingException


class Command(BaseCommand):
    SENATE_CAPACITY = 70  # TODO: CAMBIAR! por algún motivo la fuente real devuelve 70 (9/12)

    def check_current_senators(self):
        total_persons = Person.objects.count()
        if total_persons == 0:
            raise SenateLoadingException("No persons found in the database")
        active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR).count()
        if active_senators != self.SENATE_CAPACITY:
            raise SenateLoadingException(
                f"{active_senators} active senators found in the database, {self.SENATE_CAPACITY} expected"
            )

    def handle(self, *args, **options):
        self.check_current_senators()
        senators_data = SenateHistory.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(senators_data)
        written_senators = SenatorsWriter.write(linked_data)
        active_senators = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.SENATOR)
        assert len(active_senators) == self.SENATE_CAPACITY
