# Base command
from typing import List
from django.db.models import Q
from django.core.management.base import BaseCommand
import pandas as pd

# Project
from recoleccion.models.linking import DENIED_INDICATOR
import logging
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.models.vote import Vote


class Command(BaseCommand):
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        votes_without_party = Vote.objects.filter(party__isnull=True)
        unique_party_names = votes_without_party.values_list("party_name", flat=True).distinct()
        if not unique_party_names:
            self.logger.info("All votes have a party, exiting...")
            return
        self.logger.info(f"{len(unique_party_names)} unique parties found")
        self.logger.info("Sorting parties...")
        parties_votes = {
            party_name: Vote.objects.filter(Q(party_id__isnull=True) & Q(party_name=party_name)).count()
            for party_name in unique_party_names
        }
        self.logger.info(f"Votes without party: {votes_without_party.count()}")
        parties_to_link = sorted(parties_votes.items(), key=lambda x: x[1], reverse=True)
        parties_to_link = [party_name for party_name, _ in parties_to_link]
        linked_votes = self.link_parties(parties_to_link)
        self.logger.info(f"{linked_votes} votes have been updated from linking")
        self.check_actions_for_unlinked_parties()
        self.logger.info(f"{self.unlinked_votes} votes have been updated from linking")

    def load_party_to_votes(self, party_name, party):
        votes = Vote.objects.filter(party_name=party_name)
        votes.update(party=party)
        for vote in votes:
            vote.save()
        updated_votes = votes.count()
        if party:
            self.logger.info(f"{updated_votes} votes have been updated to party {party_name} with id {party.id}")
        else:
            self.logger.info(f"{updated_votes} votes from {party_name} have been updated to have NULL party")
        return votes.count()

    def load_party_to_linked_votes(self, party_row: pd.Series):
        party_id = party_row["party_id"]
        party = Party.objects.get(id=party_id) if party_id != DENIED_INDICATOR else None
        party_name = party_row["denomination"]
        linked_votes = self.load_party_to_votes(party_name, party)
        return linked_votes

    def link_parties(self, parties_to_link: List[str]) -> pd.DataFrame:
        # Tries to link the parties, unlinked parties are returned
        if not parties_to_link:
            self.unlinked_parties = pd.DataFrame()  # empty dataframe
            self.logger.info("No parties to link")
            return 0
        parties_to_link = pd.DataFrame(parties_to_link, columns=["party_name"])
        parties_to_link["id"] = None  # the linker expects an id column
        linker = PartyLinker()
        linked_data = linker.link_parties(parties_to_link)
        linked_parties = linked_data[linked_data["party_id"].notnull()]
        self.unlinked_parties = linked_data[linked_data["party_id"].isnull()]
        total_votes_linked = 0
        for _, row in linked_parties.iterrows():
            votes_linked = self.load_party_to_linked_votes(row)
            total_votes_linked += votes_linked
        return total_votes_linked

    def check_actions_for_unlinked_parties(self):
        self.unlinked_votes = 0
        if self.unlinked_parties.empty:
            self.logger.info("No unlinked parties to check")
            return
        self.unlinked_parties: List[str] = self.unlinked_parties["denomination"].unique()
        for party_name in self.unlinked_parties:
            party_created = self.check_for_party_creation(party_name)
            if party_created:
                continue
            party_denomination_created = self.check_for_party_denomination_creation(party_name)
            if party_denomination_created:
                continue
            self.logger.info(f"Votes linked to {party_name} will remain without a party")
            unlinked_votes = Vote.objects.filter(party_name=party_name).count()
            self.unlinked_votes += unlinked_votes

    def create_new_party(self, party_name):
        party = Party.objects.create(main_denomination=party_name)
        self.logger.info(f"New party {party_name} created with id {party.id}")
        return party

    def create_new_party_denomination(self, party_id, party_name):
        party = Party.objects.get(id=party_id)
        PartyDenomination.objects.create(party=party, denomination=party_name)
        self.logger.info(
            f"New denomination {party_name} created for party {party.main_denomination} with id {party_id}"
        )

    def check_for_party_creation(self, party_name: str) -> bool:
        party_created = False
        user_input = input(f"Create NEW party {party_name}? (y/n): ")
        if user_input == "y":
            party = self.create_new_party(party_name)
            self.load_party_to_votes(party_name, party)
            party_created = True
        return party_created

    def check_for_party_denomination_creation(self, party_name: str) -> bool:
        party_id = input("Party id? (empty to skip): ")
        if not party_id:
            return False

        party_id = int(party_id)
        self.create_new_party_denomination(party_id, party_name)
        party = Party.objects.get(id=party_id)
        self.load_party_to_votes(party_name, party)
        return True
