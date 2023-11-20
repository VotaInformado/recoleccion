import pandas as pd

# Base command
from django.core.management.base import BaseCommand
from django.db import transaction

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.components.data_sources.votes_source import DeputyVotesSource
from recoleccion.components.writers.votes_writer import VotesWriter
import logging
from recoleccion.models import Person, Vote


class Command(BaseCommand):
    logger = l

    def add_arguments(self, parser):
        parser.add_argument("--starting-year", type=int, default=2023)

    @transaction.atomic
    def handle(self, *args, **options):
        votes_without_person = Vote.objects.filter(person_id__isnull=True)
        unique_person_names = votes_without_person.values_list("person_name", "person_last_name", flat=False).distinct()
        for name, last_name in unique_person_names:
            # another command may have already created the person, so we check if it exists
            person = Person.objects.filter(name=name, last_name=last_name).first()
            if not person:
                self.logger.info(f"Creating person {name} {last_name}")
                person = Person.objects.create(name=name, last_name=last_name)
            else:
                self.logger.info(f"Person {name} {last_name} already exists")
            person_votes = votes_without_person.filter(person_name=name, person_last_name=last_name)
            for vote in person_votes:
                vote.person_id = person.id
                vote.save()
            self.logger.info(f"Updated {len(person_votes)} votes with person {name} {last_name} (id {person.id})")
