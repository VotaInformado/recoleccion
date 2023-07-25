# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.models.deputy_seat import DeputySeat
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat


class Command(BaseCommand):
    def handle(self, *args, **options):
        SenateSeat.objects.all().delete()
        DeputySeat.objects.all().delete()
        Person.objects.all().delete()
