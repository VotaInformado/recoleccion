# Base command
from typing import List
from django.db.models import Q
from django.core.management.base import BaseCommand
import pandas as pd

# Project
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.models.vote import Vote


class Command(BaseCommand):
    logger = CustomLogger(threading=True)

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
        sorted_parties = sorted(parties_votes.items(), key=lambda x: x[1], reverse=True)
        loaded_denominations = PartyDenomination.objects.all()
        denominations_dict = {pd.denomination: pd.party for pd in loaded_denominations}
        undefined_parties: List[str] = []
        exact_matches = 0
        self.logger.info(f"Votes without party: {votes_without_party.count()}")
        for party_name, _ in sorted_parties:
            if party_name in denominations_dict:
                party = denominations_dict[party_name]
                loaded_votes = self.load_party_to_votes(party_name, party)
                exact_matches += loaded_votes
            else:
                undefined_parties.append(party_name)
        self.logger.info(f"{exact_matches} votes have been updated from exact matches")
        case_difference_votes = self.load_case_difference_parties(undefined_parties)
        self.logger.info(f"{case_difference_votes} votes have been updated from case difference")
        linked_votes = self.link_parties(undefined_parties)
        self.logger.info(f"{linked_votes} votes have been updated from linking")
        self.check_actions_for_unlinked_parties()
        self.logger.info(f"{self.unlinked_votes} votes have been updated from linking")

    def load_case_difference_parties(self, undefined_parties: List[str]):
        votes_updated = 0
        party_denominations = PartyDenomination.objects.all()
        denominations_info = {pd.denomination.lower(): pd for pd in party_denominations}
        for party_name in undefined_parties:
            if party_name.lower() in denominations_info:
                party_denomination = denominations_info[party_name.lower()]
                party = party_denomination.party
                party_votes_updated = self.load_party_to_votes(party_name, party)
                votes_updated += party_votes_updated
        return votes_updated

    def load_party_to_votes(self, party_name, party):
        votes = Vote.objects.filter(party_name=party_name)
        votes.update(party=party)
        for vote in votes:
            vote.save()
        updated_votes = votes.count()
        self.logger.info(f"{updated_votes} votes have been updated to party {party_name} with id {party.id}")
        return votes.count()

    def load_party_to_linked_votes(self, party_row: pd.Series):
        party_id = party_row["party_id"]
        party = Party.objects.get(id=party_id)
        party_name = party_row["party_name"]  # linker changes the column name
        linked_votes = self.load_party_to_votes(party_name, party)
        return linked_votes

    def link_parties(self, undefined_parties: List[str]) -> pd.DataFrame:
        # Tries to link the undefined parties, unlinked parties are returned
        undefined_parties = pd.DataFrame(undefined_parties, columns=["party_name"])
        undefined_parties["id"] = None  # the linker expects an id column
        linker = PartyLinker()
        linked_data = linker.link_parties(undefined_parties)
        linked_parties = linked_data[linked_data["party_id"].notnull()]
        self.unlinked_parties = linked_data[linked_data["party_id"].isnull()]
        total_votes_linked = 0
        for _, row in linked_parties.iterrows():
            votes_linked = self.load_party_to_linked_votes(row)
            total_votes_linked += votes_linked
        return total_votes_linked

    def check_actions_for_unlinked_parties(self):
        self.unlinked_votes = 0
        self.unlinked_parties: List[str] = self.unlinked_parties["party_name"].unique()
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
        PartyDenomination.objects.create(party=party, denomination=party_name)
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


# TODO: Fix -> Buscar: SELECT * FROM recoleccion_vote WHERE party_id IS NULL AND party_name IN (SELECT denomination FROM recoleccion_partydenomination)
# Actualizar a mano por el problema del comando que estaba mal hecho.
