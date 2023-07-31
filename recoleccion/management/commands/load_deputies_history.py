# Base command
from django.core.management.base import BaseCommand
from django.db import transaction

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources import DeputiesHistory
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.deputies_writer import DeputiesWriter
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeats

# Exceptions
from recoleccion.exceptions.custom import DeputiesLoadingException


class Command(BaseCommand):
    DEPUTIES_CAPACITY = 257

    def check_current_deputies(self):
        total_persons = Person.objects.count()
        if total_persons == 0:
            raise DeputiesLoadingException("No persons found in the database")
        active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY).count()
        if active_deputies != self.DEPUTIES_CAPACITY:
            raise DeputiesLoadingException(
                f"{active_deputies} active deputies found in the database, {self.DEPUTIES_CAPACITY} expected"
            )

    @transaction.atomic
    def handle(self, *args, **options):
        self.check_current_deputies()
        deputies_data = DeputiesHistory.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(deputies_data)
        written_deputies = DeputiesWriter.write(linked_data)
        active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY)
        assert len(active_deputies) == self.DEPUTIES_CAPACITY
