import json

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
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting the process")
        logger.info("Process finished")
