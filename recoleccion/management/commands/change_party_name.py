import pandas as pd
from django.db import IntegrityError
import logging

# Base command
from django.core.management.base import BaseCommand

# Components
from recoleccion.models import (
    Party,
    PartyDenomination,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crea un sub partido a partir de un partido existente."

    def add_arguments(self, parser):
        parser.add_argument("--party-id", type=int)
        parser.add_argument("--new-party-name", type=str)

    def handle(self, *args, **options):
        party_id = options["party_id"]
        new_party_name = options["new_party_name"]
        party = Party.objects.get(id=party_id)
        previous_name = party.main_denomination
        if new_party_name == previous_name:
            logger.info(f"Party {party.main_denomination} already has that name")
            return
        try:
            party.save()
        except IntegrityError:
            logger.info(f"The name {new_party_name} is already taken")
            return

        PartyDenomination.objects.create(party=party, denomination=new_party_name)
        try:
            # Por si las dudas, tratamos de crear la denominación asociada al nombre anterior
            PartyDenomination.objects.create(party=party, denomination=previous_name)
        except IntegrityError:
            pass
        party.main_denomination = new_party_name
        logger.info(f"Party {party.main_denomination} has been updated")
