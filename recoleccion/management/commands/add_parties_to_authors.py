# Base command
from typing import List
from django.db.models import Q
from django.core.management.base import BaseCommand
import pandas as pd
from tqdm import tqdm

# Project
from recoleccion.models.linking import DENIED_INDICATOR
import logging
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.models import Authorship, Party, PartyDenomination


class Command(BaseCommand):
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        authors_without_party = Authorship.objects.filter(party__isnull=True)
        unique_party_names = authors_without_party.values_list("party_name", flat=True).distinct()
        if not unique_party_names:
            self.logger.info("All authors have a party, exiting...")
            return
        self.logger.info(f"{len(unique_party_names)} unique parties found")
        self.logger.info("Sorting parties...")
        parties_authors = {
            party_name: Authorship.objects.filter(Q(party_id__isnull=True) & Q(party_name=party_name)).count()
            for party_name in unique_party_names
        }
        self.logger.info(f"Authors without party: {authors_without_party.count()}")
        parties_to_link = sorted(parties_authors.items(), key=lambda x: x[1], reverse=True)
        parties_to_link = [party_name for party_name, _ in parties_to_link]
        linked_authors = self.link_parties(parties_to_link)
        self.logger.info(f"{linked_authors} authors have been updated from linking")
        self.check_actions_for_unlinked_parties()
        self.logger.info(f"{self.unlinked_authors} authors have been updated from linking")

    def load_party_to_authors(self, party_name, party):
        authors = Authorship.objects.filter(party_name=party_name)
        authors.update(party=party)
        for author in authors:
            author.save()
        updated_authors = authors.count()
        if party:
            self.logger.info(f"{updated_authors} authors have been updated to party {party_name} with id {party.id}")
        else:
            self.logger.info(f"{updated_authors} authors from {party_name} have been updated to have NULL party")
        return authors.count()

    def load_party_to_linked_authors(self, party_row: pd.Series):
        party_id = party_row["party_id"]
        party = Party.objects.get(id=party_id) if party_id != DENIED_INDICATOR else None
        party_name = party_row["denomination"]
        linked_authors = self.load_party_to_authors(party_name, party)
        return linked_authors

    def link_parties(self, parties_to_link: List[str]) -> pd.DataFrame:
        # Tries to link the parties, unlinked parties are returned
        parties_to_link = pd.DataFrame(parties_to_link, columns=["party_name"])
        if parties_to_link.empty:
            self.unlinked_parties = pd.DataFrame()  # empty dataframe
            self.logger.info("No parties to link")
            return 0
        parties_to_link["id"] = None  # the linker expects an id column
        linker = PartyLinker()
        linked_data = linker.link_parties(parties_to_link)
        linked_parties = linked_data[linked_data["party_id"].notnull()]
        self.unlinked_parties = linked_data[linked_data["party_id"].isnull()]
        total_authors_linked = 0
        for _, row in linked_parties.iterrows():
            authors_linked = self.load_party_to_linked_authors(row)
            total_authors_linked += authors_linked
        return total_authors_linked

    def check_actions_for_unlinked_parties(self):
        self.unlinked_authors = 0
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
            self.logger.info(f"Authors linked to {party_name} will remain without a party")
            unlinked_authors = Authorship.objects.filter(party_name=party_name).count()
            self.unlinked_authors += unlinked_authors

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
            self.load_party_to_authors(party_name, party)
            party_created = True
        return party_created

    def check_for_party_denomination_creation(self, party_name: str) -> bool:
        party_id = input("Party id? (empty to skip): ")
        if not party_id:
            return False

        party_id = int(party_id)
        self.create_new_party_denomination(party_id, party_name)
        party = Party.objects.get(id=party_id)
        self.load_party_to_authors(party_name, party)
        return True
