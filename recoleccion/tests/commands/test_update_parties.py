import pandas as pd
import random
import string
from django.core.management import call_command

# Project
import recoleccion.tests.test_helpers.utils as ut
from recoleccion.components.linkers.party_linker import PartyLinker
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.models import Authorship, LawProject, Party, PartyDenomination, PartyLinkingDecision, Person, Vote
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


class UpdateVotesParties(LinkingTestCase):
    def create_party_linking_decision(
        self, messy_denomination: str, canonical_denomination: str, decision: str, party_id: int = None
    ):
        party_id = party_id if decision == LinkingDecisionOptions.APPROVED else None
        PartyLinkingDecision.objects.create(
            denomination=messy_denomination,
            decision=decision,
            party_id=party_id,
        )

    def create_party_denominations(self, vote_amount: int, party: Party):
        POSSIBLE_DENOMINATIONS = [
            "EL PARTIDO JUSTICIALISTA",
            "PART. JUSTICIA",
            "PARTIDO JUSTICIALISTA MENDOZA",
            "PART. JUSTICIA SANTA FE",
            "PARTIDO JUSTICIALISTA DE LA PROVINCIA DE BUENOS AIRES",
            "PARTIDO JUSTICIALISTA DE LA PROVINCIA DE CORDOBA",
            "PART. JUSTICIA DE SANTA FE",
            "PARTIDO JUSTICIALISTA DE LA PROVINCIA DE ENTRE RIOS",
            "PART. JUSTICIA DE ENTRE RIOS",
            "PARTIDO JUSTICIALISTA DE LA PROVINCIA DE MISIONES",
        ]
        for i in range(vote_amount):
            random_denomination = random.choice(POSSIBLE_DENOMINATIONS)
            POSSIBLE_DENOMINATIONS.remove(random_denomination)
            # random_denomination = "".join(random.choices(string.ascii_uppercase, k=30))
            # No hay chance de que sea alguna de las denominaciones existentes
            PartyDenomination.objects.create(party=party, denomination=random_denomination)

    def test_update_parties_votes_with_full_match(self):
        # Expected to be linked
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
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
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (different record)
        3. Gazetteer
        """

        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        SIMILAR_NAME = "SOCIEDAD JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        ut.create_party_linking_decision(SIMILAR_NAME, PARTY_NAME, LinkingDecisionOptions.DENIED)

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
        self.assertEqual(updated_vote.party_id, None)

    def test_update_parties_votes_with_different_names(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (different record)
        3. Gazetteer
        """

        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        SIMILAR_NAME = "FRENTE PARA LA VICTORIA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        ut.create_party_linking_decision(SIMILAR_NAME, PARTY_NAME, LinkingDecisionOptions.DENIED)

        original_vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=SIMILAR_NAME, reference="Project"
        )
        self.create_party_denominations(10, party)  # hay que hacer esto xq rompe con 1 canonical record
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        linker = PartyLinker()
        linked_data = linker.link_parties(messy_data)
        writer = VotesWriter()
        writer.update_vote_parties(linked_data)
        updated_vote = Vote.objects.get(id=original_vote.id)
        self.assertEqual(updated_vote.party_id, None)

    def test_update_votes_parties_with_previous_approved_linking_decision(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (same record)
        3. Gazetteer
        """

        CANONICAL_NAME = "PARTIDO JUSTICIALISTA"
        MESSY_NAME = "PART. JUSTICIALISTA"
        party = Party.objects.create(main_denomination=CANONICAL_NAME)
        ut.create_party_linking_decision(MESSY_NAME, CANONICAL_NAME, LinkingDecisionOptions.APPROVED, party.pk)

        vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=MESSY_NAME, reference="Project"
        )
        self.create_party_denominations(10, party)
        call_command("add_parties_to_votes")
        vote.refresh_from_db()
        self.assertEqual(vote.party, party)

    def test_update_votes_parties_with_previous_denied_linking_decision(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (different record)
        3. Gazetteer
        """

        CANONICAL_NAME = "Partido Justicialista"
        MESSY_NAME = "Part. Justicialista"
        party = Party.objects.create(main_denomination=CANONICAL_NAME)
        ut.create_party_linking_decision(MESSY_NAME, CANONICAL_NAME, LinkingDecisionOptions.DENIED)
        vote = Vote.objects.create(
            person_name="Nombre", person_last_name="Apellido", party_name=MESSY_NAME, reference="Project"
        )
        self.create_party_denominations(10, party)
        call_command("add_parties_to_votes")
        vote.refresh_from_db()
        self.assertEqual(vote.party, None)


class UpdateAuthorsParties(LinkingTestCase):
    fixtures = ["person.json", "law_project.json"]

    def create_party_denominations(self, vote_amount: int, party: Party):
        POSSIBLE_DENOMINATIONS = [
            "El Partido Justicialista",
            "Part. Justicia",
            "Partido Justicialista Mendoza",
            "Part. Justicia Santa Fe",
            "Partido Justicialista de la Provincia de Buenos Aires",
            "Partido Justicialista de la Provincia de Córdoba",
            "Part. Justicia de Santa Fe",
            "Partido Justicialista de la Provincia de Entre Ríos",
            "Part. Justicia de Entre Ríos",
            "Partido Justicialista de la Provincia de Misiones",
        ]
        for i in range(vote_amount):
            random_denomination = random.choice(POSSIBLE_DENOMINATIONS)
            POSSIBLE_DENOMINATIONS.remove(random_denomination)
            # random_denomination = "".join(random.choices(string.ascii_uppercase, k=30))
            # No hay chance de que sea alguna de las denominaciones existentes
            PartyDenomination.objects.create(party=party, denomination=random_denomination)

    def test_update_authors_parties_with_exact_match(self):
        PARTY_NAME = "Partido Justicialista"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        person = Person.objects.first()
        project = LawProject.objects.first()
        author = Authorship.objects.create(
            project=project, person=person, party_name=PARTY_NAME, author_type="Diputado", source="Test"
        )
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        call_command("add_parties_to_authors")
        author.refresh_from_db()
        self.assertEqual(author.party, party)

    def create_party_linking_decision(
        self, messy_denomination: str, canonical_denomination: str, decision: str, party_id: int = None
    ):
        party_id = party_id if decision == LinkingDecisionOptions.APPROVED else None
        PartyLinkingDecision.objects.create(
            denomination=messy_denomination,
            compared_against=canonical_denomination,
            decision=decision,
            party_id=party_id,
        )

    def test_update_authors_parties_with_previous_approved_linking_decision(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (same record)
        3. Gazetteer
        """

        CANONICAL_NAME = "Partido Justicialista"
        MESSY_NAME = "Part. Justicialista"
        party = Party.objects.create(main_denomination=CANONICAL_NAME)
        ut.create_party_linking_decision(MESSY_NAME, CANONICAL_NAME, LinkingDecisionOptions.APPROVED, party.pk)
        person = Person.objects.first()
        project = LawProject.objects.first()
        author = Authorship.objects.create(
            project=project, person=person, party_name=MESSY_NAME, author_type="Diputado", source="Test"
        )
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        call_command("add_parties_to_authors")
        author.refresh_from_db()
        self.assertEqual(author.party, party)

    def test_update_authors_parties_with_previous_denied_linking_decision(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (different record)
        3. Gazetteer
        """

        CANONICAL_NAME = "Partido Justicialista"
        MESSY_NAME = "Part. Justicialista"
        party = Party.objects.create(main_denomination=CANONICAL_NAME)
        ut.create_party_linking_decision(MESSY_NAME, CANONICAL_NAME, LinkingDecisionOptions.DENIED)
        person = Person.objects.first()
        project = LawProject.objects.first()
        author = Authorship.objects.create(
            project=project, person=person, party_name=MESSY_NAME, author_type="Diputado", source="Test"
        )
        self.create_party_denominations(5, party)  # hay que hacer esto xq rompe con 1 canonical record
        call_command("add_parties_to_authors")
        author.refresh_from_db()
        self.assertEqual(author.party, None)
