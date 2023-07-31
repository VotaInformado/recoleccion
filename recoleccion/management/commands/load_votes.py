# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources.votes_source import DeputyVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.components.linkers import PersonLinker


class Command(BaseCommand):

    def handle(self, *args, **options):
        votes = DeputyVotesSource.get_data()
        linker = PersonLinker()
        linked_data = linker.link_persons(votes)
        VotesWriter.write(votes)
        
