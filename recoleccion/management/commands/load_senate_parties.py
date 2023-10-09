# Base command
from django.core.management.base import BaseCommand

# Project
from recoleccion.models import SenateSeat
from recoleccion.models.party import Party, PartyDenomination


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Asume que se corrió el de diputados primero, busca los partidos por nombre en primer lugar
        parties = SenateSeat.objects.values("party_name").distinct()
        for i, party_info in enumerate(parties):
            party_name = party_info["party_name"]
            if self.party_exists(party_name):
                party_id = self.get_party_id(party_name)
                print(f"El partido {party_name} ya existe, con id {party_id}")
                self.update_party_id(party_id, party_name)
                continue
            print(f"Ciclo: {i}")
            print(f"Partido: {party_name}")
            print("Id de partido? Vacío para cargar un nuevo partido, s para skippear")
            response = input("").lower()
            if response == "s":
                continue
            party_id = int(response) if response else None
            if party_id:
                new_denomination_response = input("Guardar nueva denominación? (y/n)")
                if new_denomination_response == "y":
                    self.create_new_party_denomination(party_id, party_name)
                self.update_party_id(party_id, party_name)
            else:
                party = self.create_new_party(party_name)
                self.update_party_id(party.id, party_name)

    def party_exists(self, party_name):
        # Check if the party exists by its main denomination or any of its alternative denominations
        party_exists = Party.objects.filter(main_denomination=party_name).exists()
        if party_exists:
            return True
        alt_denomination_exists = PartyDenomination.objects.filter(denomination=party_name).exists()
        return alt_denomination_exists

    def get_party_id(self, party_name):
        # Gets the party id by its main denomination or any of its alternative denominations
        party = Party.objects.filter(main_denomination=party_name).first()
        if party:
            return party.id
        party_denomination = PartyDenomination.objects.filter(denomination=party_name).first()
        return party_denomination.party.id

    def create_new_party_denomination(self, party_id, party_name):
        party = Party.objects.get(id=party_id)
        PartyDenomination.objects.create(party=party, denomination=party_name)

    def create_new_party(self, party_name):
        party = Party.objects.create(main_denomination=party_name)
        return party

    def update_party_id(self, party_id, party_name):
        """Receives a party_id and a party_name
        Updates the party_id of all the deputy seats with that party_name
        """
        SenateSeat.objects.filter(party_name=party_name).update(party_id=party_id)

# PARTIDO Justicialista