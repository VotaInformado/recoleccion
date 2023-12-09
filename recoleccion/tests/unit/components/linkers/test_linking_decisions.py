import random
from django.core.management import call_command
from dedupe import Gazetteer
from django.conf import settings
import pandas as pd
from recoleccion.components.linkers.linker import Linker
from recoleccion.components.writers.deputies_writer import DeputiesWriter
from recoleccion.components.writers.senators_writer import SenatorsWriter
from recoleccion.components.writers.votes_writer import VotesWriter
from recoleccion.models.authorship import Authorship
from recoleccion.models.deputy_seat import DeputySeat
from recoleccion.models.law_project import LawProject
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.models.vote import Vote

# Project
from recoleccion.management.commands.define_dubious_records import Command
import recoleccion.tests.test_helpers.utils as ut
from recoleccion.components.linkers import PartyLinker, PersonLinker
from recoleccion.models.linking.party_linking import PartyLinkingDecision
from recoleccion.models.linking.person_linking import PersonLinkingDecision
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.models.person import Person
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.tests.test_helpers.faker import create_fake_df, parties as fake_parties
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


class PersonLinkingDecisionsTestCase(LinkingTestCase):
    def setUp(self):
        self.messy_columns = {
            "name": "str",
            "last_name": "str",
            "person_id": "int",
            "province": "str",
            "start_of_term": "date",
            "end_of_term": "date",
            "party": "str",
        }
        self.canonical_columns = {
            "name": "str",
            "last_name": "str",
            "id": "int",
        }

    def create_person_linking_decision(self, messy_name: str, canonical_name: str, decision: str, person_id=1):
        person_id = person_id if decision != LinkingDecisionOptions.DENIED else None
        PersonLinkingDecision.objects.create(messy_name=messy_name, decision=decision, person_id=person_id)

    def test_saving_person_linking_decision(self):
        MESSY_NAME = "Juan C."
        MESSY_LAST_NAME = "Perez"
        CANONICAL_ID = 1

        canonical_record = {
            "name": "Juan",
            "last_name": "Perez",
            "id": CANONICAL_ID,
        }
        updated_record = {
            "name": MESSY_NAME,
            "last_name": MESSY_LAST_NAME,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_index = len(canonical_data) + 1
        canonical_data[canonical_index] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index = len(updated_data)
        updated_data.loc[messy_index] = updated_record
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [messy_index]
        expected_dubious_matches = len(settings.MESSY_INDEXES)
        settings.CANONICAL_INDEXES = [canonical_index]
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
                linker = PersonLinker()
                linked_data = linker.link_persons(updated_data)

        pending_linking_decisions = PersonLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING)
        self.assertEqual(len(pending_linking_decisions), expected_dubious_matches)
        pending_decision = pending_linking_decisions[0]
        expected_full_name = f"{MESSY_NAME} {MESSY_LAST_NAME}"
        self.assertEqual(pending_decision.messy_name, expected_full_name)
        self.assertEqual(pending_decision.person_id, CANONICAL_ID)
        pending_decision_id = pending_decision.uuid
        pending_record = linked_data[
            (linked_data["name"] == MESSY_NAME) & (linked_data["last_name"] == MESSY_LAST_NAME)
        ].iloc[0]
        self.assertEqual(pending_record["linking_id"], pending_decision_id)
        non_pending_records = linked_data[linked_data["linking_id"] != pending_decision_id]
        self.assertEqual(len(non_pending_records), len(linked_data) - expected_dubious_matches)

    def test_saving_the_same_linking_decision_for_different_persons(self):
        MESSY_NAME = "Juan C."
        MESSY_LAST_NAME = "Perez"
        CANONICAL_ID = 1

        canonical_record = {
            "name": "Juan",
            "last_name": "Perez",
            "id": CANONICAL_ID,
        }
        updated_record_1 = {
            "name": MESSY_NAME,
            "last_name": MESSY_LAST_NAME,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }
        updated_record_2 = {
            "name": MESSY_NAME,
            "last_name": MESSY_LAST_NAME,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }
        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_index = len(canonical_data) + 1
        canonical_data[canonical_index] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index_1, messy_index_2 = len(updated_data) - 1, len(updated_data)
        updated_data.loc[messy_index_1] = updated_record_1
        updated_data.loc[messy_index_2] = updated_record_2
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [messy_index_1, messy_index_2]
        expected_dubious_matches = len(settings.MESSY_INDEXES)
        settings.CANONICAL_INDEXES = [canonical_index, canonical_index]
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
                linker = PersonLinker()
                linked_data = linker.link_persons(updated_data)

        pending_linking_decisions = PersonLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING)
        self.assertEqual(len(pending_linking_decisions), 1)  # only one pending decision should have been created
        pending_decision = pending_linking_decisions[0]
        expected_full_name = f"{MESSY_NAME} {MESSY_LAST_NAME}"
        self.assertEqual(pending_decision.messy_name, expected_full_name)
        self.assertEqual(pending_decision.person_id, CANONICAL_ID)
        pending_decision_id = pending_decision.uuid
        pending_records = linked_data[
            (linked_data["name"] == MESSY_NAME) & (linked_data["last_name"] == MESSY_LAST_NAME)
        ]
        for _, pending_record in pending_records.iterrows():
            self.assertEqual(pending_record["linking_id"], pending_decision_id)
        non_pending_records = linked_data[linked_data["linking_id"] != pending_decision_id]
        self.assertEqual(len(non_pending_records), len(linked_data) - expected_dubious_matches)

    def test_updating_records_person_after_approved_linking_decision(self):
        call_command("loaddata", "person.json")
        # We leave only 10 persons
        ids_to_keep = list(Person.objects.order_by("id")[:10].values_list("id", flat=True))
        Person.objects.exclude(id__in=ids_to_keep).delete()
        MESSY_NAME = "Juan C."
        MESSY_LAST_NAME = "Perez"
        updated_record = {
            "name": MESSY_NAME,
            "last_name": MESSY_LAST_NAME,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
            "party": "Frente de Todos",
        }

        linker = PersonLinker()
        canonical_index = 0
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index = len(updated_data)
        updated_data.loc[messy_index] = updated_record
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [messy_index]
        settings.CANONICAL_INDEXES = [canonical_index]
        with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
            with mck.mock_method_side_effect(PersonLinker, "load_exact_matches", mck.mock_load_exact_matches):
                linked_data = linker.link_persons(updated_data)
        SenatorsWriter.write(linked_data)
        linked_data.rename(columns={"province": "district"}, inplace=True)
        DeputiesWriter.write(linked_data)
        pending_decision = PersonLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING).first()
        canonical_id = pending_decision.person_id
        self.assertEqual(pending_decision.messy_name, f"{MESSY_NAME} {MESSY_LAST_NAME}")
        with mck.mock_method(Command, "ask_for_user_decision", return_value=LinkingDecisionOptions.APPROVED):
            call_command("define_dubious_records")
        pending_decision.refresh_from_db()
        self.assertEqual(pending_decision.decision, LinkingDecisionOptions.APPROVED)
        senator = SenateSeat.objects.filter(linking_id=pending_decision.uuid).first()
        self.assertEqual(senator.person.pk, canonical_id)
        deputy = DeputySeat.objects.filter(linking_id=pending_decision.uuid).first()
        self.assertEqual(deputy.person.pk, canonical_id)

    def test_updating_person_linking_decision_records_individually(self):
        person = Person.objects.create(name="Juan", last_name="Perez")
        vote = Vote.objects.create(person_name="Juan", person_last_name="Perez")
        linking_decision = PersonLinkingDecision.objects.create(
            messy_name="Juan Perez", decision=LinkingDecisionOptions.PENDING, person=person
        )
        authorship = Authorship.objects.create(person_name="Juan", person_last_name="Perez")
        vote.linking_id = linking_decision.uuid
        vote.save()
        authorship.linking_id = linking_decision.uuid
        authorship.save()
        records = linking_decision._get_related_records()
        linking_decision._update_records_individually(records)
        vote.refresh_from_db()
        authorship.refresh_from_db()
        self.assertEqual(vote.person.pk, person.pk)
        self.assertEqual(authorship.person.pk, person.pk)


class PartyLinkingDecisionsTestCase(LinkingTestCase):
    fixtures = ["law_project.json"]

    def setUp(self):
        self.messy_columns = {
            "name": "str",
            "last_name": "str",
            "person_id": "int",
            "province": "str",
            "start_of_term": "date",
            "end_of_term": "date",
            "party": "str",
        }
        self.canonical_columns = {
            "name": "str",
            "last_name": "str",
            "id": "int",
        }

    def create_party_denominations(self, vote_amount: int, party: Party):
        possible_denominations = fake_parties.copy()
        for i in range(vote_amount):
            random_denomination = random.choice(possible_denominations)
            possible_denominations.remove(random_denomination)
            # random_denomination = "".join(random.choices(string.ascii_uppercase, k=30))
            # No hay chance de que sea alguna de las denominaciones existentes
            PartyDenomination.objects.create(party=party, denomination=random_denomination)

    def test_saving_party_linking_decision(self):
        settings.REAL_METHOD = Gazetteer.search
        messy_index = 0
        settings.MESSY_INDEXES = [messy_index]  # these are the indexes of the pending decisions messy records
        canonical_index = 0
        settings.CANONICAL_INDEXES = [0]  # these are the indexes of the pending decisions canonical records
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        self.create_party_denominations(25, party)  # hay que hacer esto xq rompe con 1 canonical record
        linker = PartyLinker()
        canonical_party_id = linker.get_canonical_data()[canonical_index]["party_id"]
        # id of the canonical record's party
        TOTAL_MESSY_RECORDS = 10
        projects = LawProject.objects.all()[:TOTAL_MESSY_RECORDS]
        messy_parties = create_fake_df({"party_name": "party"}, n=TOTAL_MESSY_RECORDS)
        for i in range(TOTAL_MESSY_RECORDS):
            Vote.objects.create(
                person_name="Nombre", person_last_name="Apellido", party_name=messy_parties[i], project=projects[i]
            )
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
            linked_data = linker.link_parties(messy_data)
        non_linked_rows = linked_data[pd.isna(linked_data["linking_id"])]
        self.assertEqual(len(non_linked_rows), len(linked_data) - 1)
        uuid = linked_data.iloc[messy_index]["linking_id"]
        pending_decision = PartyLinkingDecision.objects.get(uuid=uuid)
        pending_decision_party = pending_decision.party
        self.assertEqual(pending_decision_party.pk, canonical_party_id)

    def test_saving_the_same_linking_decision_for_identical_messy_parties(self):
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [0, 1]  # these are the indexes of the pending decisions messy records
        canonical_index = 0
        settings.CANONICAL_INDEXES = [0, 0]  # these are the indexes of the pending decisions canonical records
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        self.create_party_denominations(25, party)  # hay que hacer esto xq rompe con 1 canonical record
        linker = PartyLinker()
        canonical_party_id = linker.get_canonical_data()[canonical_index]["party_id"]
        # id of the canonical record's party
        TOTAL_MESSY_RECORDS = 10
        projects = LawProject.objects.all()[:TOTAL_MESSY_RECORDS]
        messy_parties = create_fake_df({"party_name": "party"}, n=TOTAL_MESSY_RECORDS, as_dict=False)
        messy_parties.at[1, "party_name"] = messy_parties.at[0, "party_name"]
        messy_parties = messy_parties.to_dict(orient="records")
        for i in range(TOTAL_MESSY_RECORDS):
            Vote.objects.create(
                person_name="Nombre", person_last_name="Apellido", party_name=messy_parties[i], project=projects[i]
            )
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
            linked_data = linker.link_parties(messy_data)
        non_linked_rows = linked_data[pd.isna(linked_data["linking_id"])]
        expected_linking_decisions = len(settings.MESSY_INDEXES)
        self.assertEqual(len(non_linked_rows), len(linked_data) - expected_linking_decisions)
        messy_index = random.choice(settings.MESSY_INDEXES)
        uuid = linked_data.iloc[messy_index]["linking_id"]
        total_pending_decisions = PartyLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING).count()
        self.assertEqual(total_pending_decisions, 1)  # only one decision is created, used for both messy records
        pending_decision = PartyLinkingDecision.objects.get(uuid=uuid)
        pending_decision_party = pending_decision.party
        self.assertEqual(pending_decision_party.pk, canonical_party_id)

    def test_updating_votes_party_after_approved_linking_decision(self):
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [0, 1]  # these are the indexes of the pending decisions messy records
        canonical_index = 0
        settings.CANONICAL_INDEXES = [0, 0]  # these are the indexes of the pending decisions canonical records
        PARTY_NAME = "PARTIDO JUSTICIALISTA"
        party = Party.objects.create(main_denomination=PARTY_NAME)
        self.create_party_denominations(25, party)  # hay que hacer esto xq rompe con 1 canonical record
        linker = PartyLinker()
        canonical_party_id = linker.get_canonical_data()[canonical_index]["party_id"]
        # id of the canonical record's party
        TOTAL_MESSY_RECORDS = 10
        projects = LawProject.objects.all()[:TOTAL_MESSY_RECORDS]
        messy_parties = create_fake_df({"party_name": "party_unique"}, n=TOTAL_MESSY_RECORDS, as_dict=False)
        messy_parties.at[1, "party_name"] = messy_parties.at[0, "party_name"]
        messy_parties = messy_parties.to_dict(orient="records")
        for i in range(TOTAL_MESSY_RECORDS):
            Vote.objects.create(
                person_name="Nombre", person_last_name="Apellido", party_name=messy_parties[i]["party_name"], project=projects[i]
            )
        queryset = Vote.objects.values("party_name", "id")
        messy_data = pd.DataFrame(list(queryset))
        with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
            with mck.mock_method_side_effect(PartyLinker, "load_exact_matches", mck.mock_load_exact_matches):
                linked_data = linker.link_parties(messy_data)
        non_linked_rows = linked_data[pd.isna(linked_data["linking_id"])]
        expected_linking_decisions = len(settings.MESSY_INDEXES)
        self.assertEqual(len(non_linked_rows), len(linked_data) - expected_linking_decisions)
        messy_index = random.choice(settings.MESSY_INDEXES)
        uuid = linked_data.iloc[messy_index]["linking_id"]
        total_pending_decisions = PartyLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING).count()
        self.assertEqual(total_pending_decisions, 1)  # only one decision is created, used for both messy records
        pending_decision = PartyLinkingDecision.objects.get(uuid=uuid)
        pending_decision_party = pending_decision.party
        self.assertEqual(pending_decision_party.pk, canonical_party_id)
        with mck.mock_method(Command, "ask_for_user_decision", return_value=LinkingDecisionOptions.APPROVED):
            call_command("define_dubious_records")
        pending_decision.refresh_from_db()
        self.assertEqual(pending_decision.decision, LinkingDecisionOptions.APPROVED)
        votes = Vote.objects.filter(linking_id=pending_decision.uuid)
        for vote in votes:
            self.assertEqual(vote.party.pk, canonical_party_id)

    def test_updating_party_linking_decision_records_individually(self):
        party = Party.objects.create(main_denomination="Partido Justicialista")
        vote = Vote.objects.create(party_name="Partido Justicialista")
        linking_decision = PartyLinkingDecision.objects.create(
            messy_denomination="Juan Perez", decision=LinkingDecisionOptions.PENDING, party=party
        )
        authorship = Authorship.objects.create(party_name="Partido Justicialista")
        vote.linking_id = linking_decision.uuid
        vote.save()
        authorship.linking_id = linking_decision.uuid
        authorship.save()
        records = linking_decision._get_related_records()
        linking_decision._update_records_individually(records)
        vote.refresh_from_db()
        authorship.refresh_from_db()
        self.assertEqual(vote.party.pk, party.pk)
        self.assertEqual(authorship.party.pk, party.pk)
