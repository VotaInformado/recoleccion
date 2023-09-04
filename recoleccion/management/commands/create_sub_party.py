import pandas as pd

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.day_orders_source import DeputiesDayOrderSource
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter
from recoleccion.models import DeputySeat, Party, PartyDenomination, PartyRelationTypes, SenateSeat
from recoleccion.utils.custom_logger import CustomLogger


class Command(BaseCommand):
    logger = CustomLogger()
    help = "Crea un sub partido a partir de un partido existente."

    def add_arguments(self, parser):
        parser.add_argument("--party-id", type=int)
        parser.add_argument("--sub-party-id", type=int)
        parser.add_argument("--relation-type", type=str, default=PartyRelationTypes.SUB_PARTY)

    def handle(self, *args, **options):
        party_id = options["party_id"]
        sub_party_id = options["sub_party_id"]
        relation_type = options["relation_type"]
        party = Party.objects.get(id=party_id)
        sub_party = Party.objects.get(id=sub_party_id)
        self.logger.info(f"Party: {party.main_denomination}")
        self.logger.info(f"Sub party: {sub_party.main_denomination}")
        sub_party_senate_seats = SenateSeat.objects.filter(party_id=sub_party_id)
        sub_party_deputy_seats = DeputySeat.objects.filter(party_id=sub_party_id)
        self.logger.info(f"Updated {len(sub_party_senate_seats)} senate seats")
        sub_party_senate_seats.update(party_id=party_id)
        self.logger.info(f"Updated {len(sub_party_deputy_seats)} deputy seats")
        sub_party_deputy_seats.update(party_id=party_id)
        PartyDenomination.objects.create(
            party=party, denomination=sub_party.main_denomination, relation_type=relation_type
        )
        sub_party.delete()
        self.logger.info(f"Deleted sub party {sub_party.main_denomination}")
