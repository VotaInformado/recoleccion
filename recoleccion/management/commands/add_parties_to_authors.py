# Base command
from typing import List
from django.db.models import Q
from django.core.management.base import BaseCommand
import pandas as pd
from tqdm import tqdm

# Project
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.models import Authorship, Party, PartyDenomination


class Command(BaseCommand):
    logger = CustomLogger(threading=True)

    def handle(self, *args, **options):
        self.fix_authors_parties_case()
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
        sorted_parties = sorted(parties_authors.items(), key=lambda x: x[1], reverse=True)
        loaded_denominations = PartyDenomination.objects.all()
        denominations_dict = {pd.denomination: pd.party for pd in loaded_denominations}
        undefined_parties: List[str] = []
        exact_matches = 0
        self.logger.info(f"Authors without party: {authors_without_party.count()}")
        for party_name, _ in sorted_parties:
            if party_name in denominations_dict:
                party = denominations_dict[party_name]
                loaded_authors = self.load_party_to_authors(party_name, party)
                exact_matches += loaded_authors
            else:
                undefined_parties.append(party_name)
        self.logger.info(f"{exact_matches} authors have been updated from exact matches")
        case_difference_authors = self.load_case_difference_parties(undefined_parties)
        self.logger.info(f"{case_difference_authors} authors have been updated from case difference")
        linked_authors = self.link_parties(undefined_parties)
        self.logger.info(f"{linked_authors} authors have been updated from linking")
        self.check_actions_for_unlinked_parties()
        self.logger.info(f"{self.unlinked_authors} authors have been updated from linking")

    def fix_authors_parties_case(self):
        # Sets all the party_names of the Authorship table to Capitalized
        self.logger.info("Fixing authors parties case...")
        authors = Authorship.objects.all()
        for author in tqdm(authors):
            author.party_name = author.party_name.capitalize()
            author.save()

    def load_case_difference_parties(self, undefined_parties: List[str]):
        authors_updated = 0
        party_denominations = PartyDenomination.objects.all()
        denominations_info = {pd.denomination.lower(): pd for pd in party_denominations}
        for party_name in undefined_parties:
            if party_name.lower() in denominations_info:
                party_denomination = denominations_info[party_name.lower()]
                party = party_denomination.party
                party_authors_updated = self.load_party_to_authors(party_name, party)
                authors_updated += party_authors_updated
        return authors_updated

    def load_party_to_authors(self, party_name, party):
        authors = Authorship.objects.filter(party_name=party_name)
        authors.update(party=party)
        for author in authors:
            author.save()
        updated_authors = authors.count()
        self.logger.info(f"{updated_authors} authors have been updated to party {party_name} with id {party.id}")
        return authors.count()

    def load_party_to_linked_authors(self, party_row: pd.Series):
        party_id = party_row["party_id"]
        party = Party.objects.get(id=party_id)
        party_name = party_row["denomination"]  # linker changes the column name
        linked_authors = self.load_party_to_authors(party_name, party)
        return linked_authors

    def link_parties(self, undefined_parties: List[str]) -> pd.DataFrame:
        # Tries to link the undefined parties, unlinked parties are returned
        undefined_parties = pd.DataFrame(undefined_parties, columns=["party_name"])
        undefined_parties["id"] = None  # the linker expects an id column
        linker = PartyLinker()
        linked_data = linker.link_parties(undefined_parties)
        linked_parties = linked_data[linked_data["party_id"].notnull()]
        self.unlinked_parties = linked_data[linked_data["party_id"].isnull()]
        total_authors_linked = 0
        for _, row in linked_parties.iterrows():
            authors_linked = self.load_party_to_linked_authors(row)
            total_authors_linked += authors_linked
        return total_authors_linked

    def check_actions_for_unlinked_parties(self):
        self.unlinked_authors = 0
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
