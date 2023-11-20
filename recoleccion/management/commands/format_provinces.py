import pandas as pd
from django.db import IntegrityError

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction
from django.db.models import F

# Components
from recoleccion.models import DeputySeat, SenateSeat, Vote
from recoleccion.utils.enums.provinces import Provinces
import logging
from tqdm import tqdm


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Formatea las provincias en Votos, DeputySeats y SenateSeats."

    def handle(self, *args, **options):
        self.logger.info("Starting formatting DeputySeatys provinces")
        deputy_seats = DeputySeat.objects.all()
        for deputy_seat in tqdm(deputy_seats):
            deputy_seat.district = Provinces.get_choice(deputy_seat.district)
            deputy_seat.save()
        self.logger.info("Finished formatting DeputySeats provinces")

        self.logger.info("Starting formatting SenateSeats provinces")
        senate_seats = SenateSeat.objects.all()
        for senate_seat in tqdm(senate_seats):
            senate_seat.province = Provinces.get_choice(senate_seat.province)
            senate_seat.save()
        self.logger.info("Finished formatting SenateSeats provinces")

        self.logger.info("Starting formatting votes provinces")
        self.logger.info("Loading votes...")
        votes = Vote.objects.all()
        for vote in tqdm(votes):
            vote.province = Provinces.get_choice(vote.province) if vote.province else None
        # Use bulk_update to update all the votes at once
        self.logger.info("Saving changes...")
        Vote.objects.bulk_update(votes, ["province"], 200)
        self.logger.info("Finished formatting provinces")
