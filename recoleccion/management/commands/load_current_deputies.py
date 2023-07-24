# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources import CurrentDeputies
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.deputies_writer import DeputiesWriter
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class Command(BaseCommand):
    DIPUTIES_CAPACITY = 257

    def handle(self, *args, **options):
        deputies_data = CurrentDeputies.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(deputies_data)
        written_deputies = DeputiesWriter.write(linked_data)
        active_deputies = Person.objects.filter(is_active=True, last_seat=LegislatorSeats.DEPUTY)
        assert len(active_deputies) == self.DIPUTIES_CAPACITY
