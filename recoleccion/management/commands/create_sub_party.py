import pandas as pd
from django.db import IntegrityError

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.models import (
    Authorship,
    DeputySeat,
    Party,
    PartyDenomination,
    PartyLinkingDecision,
    PartyRelationTypes,
    SenateSeat,
    Vote,
)
import logging


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    help = "Crea un sub partido a partir de un partido existente."

    def add_arguments(self, parser):
        parser.add_argument("--party-id", type=int)
        parser.add_argument("--sub-party-id", type=int)
        parser.add_argument("--relation-type", type=str, default=PartyRelationTypes.ALTERNATIVE_DENOMINATION)

    def handle(self, *args, **options):
        party_id = options["party_id"]
        sub_party_id = options["sub_party_id"]
        relation_type = options["relation_type"]
        party = Party.objects.get(id=party_id)
        self.logger.info(f"Party: {party.main_denomination}")
        sub_party = Party.objects.filter(id=sub_party_id).first()
        if not sub_party:
            self.logger.info(f"Sub party {sub_party_id} has already been deleted...")
        else:
            self.logger.info(f"Sub party: {sub_party.main_denomination}")
        sub_party_senate_seats = SenateSeat.objects.filter(party_id=sub_party_id)
        sub_party_deputy_seats = DeputySeat.objects.filter(party_id=sub_party_id)
        sub_party_votes = Vote.objects.filter(party_id=sub_party_id)
        sub_party_autorships = Authorship.objects.filter(party_id=sub_party_id)
        sub_party_linking_decisions = PartyLinkingDecision.objects.filter(party_id=sub_party_id)
        self.logger.info(f"Updated {len(sub_party_senate_seats)} senate seats")
        sub_party_senate_seats.update(party_id=party_id)
        self.logger.info(f"Updated {len(sub_party_deputy_seats)} deputy seats")
        sub_party_deputy_seats.update(party_id=party_id)
        self.logger.info(f"Updated {len(sub_party_votes)} votes")
        sub_party_votes.update(party_id=party_id)
        self.logger.info(f"Updated {len(sub_party_autorships)} authorships")
        sub_party_autorships.update(party_id=party_id)
        self.logger.info(f"Updated {len(sub_party_linking_decisions)} linking decisions")
        sub_party_linking_decisions.update(party_id=party_id)
        if not sub_party:
            return
        sub_party.delete()
        try:
            PartyDenomination.objects.create(
                party=party, denomination=sub_party.main_denomination, relation_type=relation_type
            )
        except IntegrityError:
            self.logger.info(f"Sub party {sub_party.main_denomination} already exists")
        self.logger.info(f"Deleted sub party {sub_party.main_denomination}")
