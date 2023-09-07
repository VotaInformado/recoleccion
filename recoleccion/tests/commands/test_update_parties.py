import pandas as pd
import random
import string

# Project
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.models.vote import Vote
from recoleccion.tests.test_helpers.test_case import LinkingTestCase


class UpdateVotesParties(LinkingTestCase):
    fixtures = ["party_linking.json"]

    def create_party_denominations(self, vote_amount: int, party: Party):
        for i in range(vote_amount):
            random_denomination = "".join(random.choices(string.ascii_uppercase, k=30))
            # No hay chance de que sea alguna de las denominaciones existentes
            PartyDenomination.objects.create(party=party, denomination=random_denomination)

    def test_update_parties_votes_with_full_match(self):
        # Expected to be linked
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        PartyDenomination.objects.create(party=party, denomination=PARTY_NAME)
        original_vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=PARTY_NAME, reference="Project"
        )
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        linker = PartyLinker()
        linked_data = linker.link_parties(messy_data)
        writer = VotesWriter()
        writer.update_vote_parties(linked_data)
        updated_vote = Vote.objects.get(id=original_vote.id)
        self.assertEqual(updated_vote.party_id, party.id)

    def test_update_parties_votes_with_very_similar_party_names(self):
        # Expected to be linked
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        SIMILAR_NAME = "PART. JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        PartyDenomination.objects.create(party=party, denomination=PARTY_NAME)
        original_vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=SIMILAR_NAME, reference="Project"
        )
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        linker = PartyLinker()
        linked_data = linker.link_parties(messy_data)
        writer = VotesWriter()
        writer.update_vote_parties(linked_data)
        updated_vote = Vote.objects.get(id=original_vote.id)
        self.assertEqual(updated_vote.party_id, party.id)

    def test_update_parties_votes_with_similar_party_names(self):
        # Expected not to be linked
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        SIMILAR_NAME = "SOCIEDAD JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        PartyDenomination.objects.create(party=party, denomination=PARTY_NAME)
        original_vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=SIMILAR_NAME, reference="Project"
        )
        import pdb

        pdb.set_trace()
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        linker = PartyLinker()
        linked_data = linker.link_parties(messy_data)
        writer = VotesWriter()
        writer.update_vote_parties(linked_data)
        updated_vote = Vote.objects.get(id=original_vote.id)
        self.assertEqual(updated_vote.party_id, None)

    # def test_update_parties_votes_with_different_names(self):
    #     # Expected not to be linked
    #     import pdb; pdb.set_trace()
    #     PARTY_NAME = "FRENTE PARA LA VICTORIA"
    #     SIMILAR_NAME = "PARTIDO JUSTICIALISTA"
    #     party = Party.objects.create(main_denomination=PARTY_NAME)
    #     PartyDenomination.objects.create(party=party, denomination=PARTY_NAME)
    #     original_vote = Vote.objects.create(
    #         person_name="Nombre", person_last_name="Apellido", party_name=SIMILAR_NAME, reference="Project"
    #     )
    #     self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
    #     queryset = Vote.objects.values("party_name", "id")
    #     messy_data = pd.DataFrame(list(queryset))
    #     linker = PartyLinker()
    #     linked_data = linker.link_parties(messy_data)
    #     writer = VotesWriter()
    #     writer.update_vote_parties(linked_data)
    #     updated_vote = Vote.objects.get(id=original_vote.id)
    #     self.assertEqual(updated_vote.party_id, None)
