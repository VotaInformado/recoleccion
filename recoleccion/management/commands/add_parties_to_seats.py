# Base command
from typing import List
from django.db.models import Q
from django.core.management.base import BaseCommand
import pandas as pd

# Project
from recoleccion.models import DeputySeat, SenateSeat
from recoleccion.models.linking import DENIED_INDICATOR
import logging
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class Command(BaseCommand):
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        deputy_seats_without_party = DeputySeat.objects.filter(party__isnull=True)
        unique_party_names = deputy_seats_without_party.values_list("party_name", flat=True).distinct()
        if not unique_party_names:
            self.logger.info("All deputy seats have a party, continuing...")
        else:
            self._handle(unique_party_names, LegislatorSeats.DEPUTY)
        senate_seats_without_party = SenateSeat.objects.filter(party__isnull=True)
        unique_party_names = senate_seats_without_party.values_list("party_name", flat=True).distinct()
        if not unique_party_names:
            self.logger.info("All senate seats have a party, exiting...")
        else:
            self._handle(unique_party_names, LegislatorSeats.SENATOR)

    def _handle(self, parties_names, seat_type):
        self.logger.info(f"{len(parties_names)} unique parties found of type {seat_type}")
        if seat_type == LegislatorSeats.DEPUTY:
            parties_seats = {
                party_name: DeputySeat.objects.filter(party_name=party_name).count() for party_name in parties_names
            }
        else:
            parties_seats = {
                party_name: SenateSeat.objects.filter(party_name=party_name).count() for party_name in parties_names
            }
        self.logger.info("Sorting parties...")
        parties_to_link = sorted(parties_seats.items(), key=lambda x: x[1], reverse=True)
        parties_to_link = [party_name for party_name, _ in parties_to_link]
        linked_seats = self.link_parties(parties_to_link, seat_type)
        self.logger.info(f"{linked_seats} {seat_type} seats have been updated from linking")
        self.check_actions_for_unlinked_parties(seat_type)
        self.logger.info(f"{self.unlinked_seats} {seat_type} seats have been updated from linking")

    def load_party_to_seats(self, party_name, party, seat_type):
        if seat_type == LegislatorSeats.DEPUTY:
            seats = DeputySeat.objects.filter(party_name=party_name)
        else:
            seats = SenateSeat.objects.filter(party_name=party_name)
        updated_seats = seats.count()
        seats.update(party=party)
        if party:
            self.logger.info(
                f"{updated_seats} {seat_type} seats have been updated to party {party_name} with id {party.id}"
            )
        else:
            self.logger.info(
                f"{updated_seats} {seat_type} seats from {party_name} have been updated to have NULL party"
            )
        return updated_seats

    def load_party_to_linked_seats(self, party_row: pd.Series, seat_type: LegislatorSeats):
        party_id = party_row["party_id"]
        party = Party.objects.get(id=party_id) if party_id != DENIED_INDICATOR else None
        party_name = party_row["denomination"]
        linked_seats = self.load_party_to_seats(party_name, party, seat_type)
        return linked_seats

    def link_parties(self, parties_to_link: List[str], seat_type: LegislatorSeats) -> pd.DataFrame:
        # Tries to link the parties, unlinked parties are returned
        if not parties_to_link:
            self.unlinked_parties = pd.DataFrame()  # empty dataframe
            self.logger.info("No parties to link")
            return 0
        parties_to_link = pd.DataFrame(parties_to_link, columns=["party_name"])
        parties_to_link["id"] = None  # the linker expects an id column
        linker = PartyLinker()
        linked_data = linker.link_parties(parties_to_link, save_original_denominations=True)
        linked_parties = linked_data[linked_data["party_id"].notnull()]
        self.unlinked_parties = linked_data[linked_data["party_id"].isnull()]
        total_seats_linked = 0
        for _, row in linked_parties.iterrows():
            seats_linked = self.load_party_to_linked_seats(row, seat_type)
            total_seats_linked += seats_linked
        return total_seats_linked

    def check_actions_for_unlinked_parties(self, seat_type: LegislatorSeats):
        self.unlinked_seats = 0
        if self.unlinked_parties.empty:
            self.logger.info("No unlinked parties to check")
            return
        self.unlinked_parties: List[str] = self.unlinked_parties["denomination"].unique()
        for party_name in self.unlinked_parties:
            party_created = self.check_for_party_creation(party_name, seat_type)
            if party_created:
                continue
            party_denomination_created = self.check_for_party_denomination_creation(party_name, seat_type)
            if party_denomination_created:
                continue
            self.logger.info(f"Seats linked to {party_name} will remain without a party")
            if seat_type == LegislatorSeats.DEPUTY:
                unlinked_seats = DeputySeat.objects.filter(party_name=party_name).count()
            else:
                unlinked_seats = SenateSeat.objects.filter(party_name=party_name).count()
            self.unlinked_seats += unlinked_seats

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

    def check_for_party_creation(self, party_name: str, seat_type: LegislatorSeats) -> bool:
        party_created = False
        user_input = input(f"Create NEW party {party_name}? (y/n): ")
        if user_input == "y":
            party = self.create_new_party(party_name)
            self.load_party_to_seats(party_name, party, seat_type)
            party_created = True
        return party_created

    def check_for_party_denomination_creation(self, party_name, seat_type: LegislatorSeats) -> bool:
        party_id = input("Party id? (empty to skip): ")
        if not party_id:
            return False

        party_id = int(party_id)
        self.create_new_party_denomination(party_id, party_name)
        party = Party.objects.get(id=party_id)
        self.load_party_to_seats(party_name, party, seat_type)
        return True
