import pandas as pd
from django.db import IntegrityError

# Base command
from django.core.management.base import BaseCommand, CommandParser

# Django

# Components
import logging
from recoleccion.components.data_sources.pictures_source import LegislatorsPictureSource
from recoleccion.components.linkers.person_linker import PersonLinker
from recoleccion.components.writers.persons_writer import PersonsWriter


class Command(BaseCommand):
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        linker = PersonLinker()
        data = LegislatorsPictureSource.get_data()
        linked_data = linker.link_persons(data)
        PersonsWriter.update_social_data(linked_data)
