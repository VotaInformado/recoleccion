from django.core.management import call_command
from dedupe import Gazetteer
from django.conf import settings

# Project
import recoleccion.tests.test_helpers.utils as ut
from recoleccion.components.linkers import PartyLinker, PersonLinker
from recoleccion.models.linking.party_linking import PartyLinkingDecision
from recoleccion.models.linking.person_linking import PersonLinkingDecision
from recoleccion.models.party import Party, PartyDenomination
from recoleccion.models.person import Person
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.tests.test_helpers.faker import create_fake_df
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


class PersonLinkerTestCase(LinkingTestCase):
    def setUp(self):
        self.messy_columns = {
            "name": "str",
            "last_name": "str",
            "person_id": "int",
            "province": "str",
            "start_of_term": "date",
            "end_of_term": "date",
        }
        self.canonical_columns = {
            "name": "str",
            "last_name": "str",
            "id": "int",
        }

    # def create_person_linking_decision(self, messy_name: str, canonical_name: str, decision: str, person_id=1):
    #     person_id = person_id if decision != LinkingDecisions.DENIED else None
    #     PersonLinkingDecision.objects.create(
    #         messy_name=messy_name, compared_against=canonical_name, decision=decision, person_id=person_id
    #     )

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
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index = len(updated_data)
        updated_data.loc[messy_index] = updated_record
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [messy_index]
        expected_dubious_matches = len(settings.MESSY_INDEXES)
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
                linker = PersonLinker()
                linked_data = linker.link_persons(updated_data)

        pending_linking_decisions = PersonLinkingDecision.objects.filter(decision=LinkingDecisions.PENDING)
        self.assertEqual(len(pending_linking_decisions), expected_dubious_matches)
        pending_decision = pending_linking_decisions[0]
        expected_full_name = f"{MESSY_NAME} {MESSY_LAST_NAME}"
        self.assertEqual(pending_decision.messy_name, expected_full_name)
        self.assertEqual(pending_decision.person_id, CANONICAL_ID)
        pending_decision_id = pending_decision.id
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
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index_1, messy_index_2 = len(updated_data) - 1, len(updated_data)
        updated_data.loc[messy_index_1] = updated_record_1
        updated_data.loc[messy_index_2] = updated_record_2
        settings.REAL_METHOD = Gazetteer.search
        settings.MESSY_INDEXES = [messy_index_1, messy_index_2]
        expected_dubious_matches = len(settings.MESSY_INDEXES)
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
                linker = PersonLinker()
                linked_data = linker.link_persons(updated_data)

        pending_linking_decisions = PersonLinkingDecision.objects.filter(decision=LinkingDecisions.PENDING)
        self.assertEqual(len(pending_linking_decisions), 1)  # only one pending decision should have been created
        pending_decision = pending_linking_decisions[0]
        expected_full_name = f"{MESSY_NAME} {MESSY_LAST_NAME}"
        self.assertEqual(pending_decision.messy_name, expected_full_name)
        self.assertEqual(pending_decision.person_id, CANONICAL_ID)
        pending_decision_id = pending_decision.id
        pending_records = linked_data[
            (linked_data["name"] == MESSY_NAME) & (linked_data["last_name"] == MESSY_LAST_NAME)
        ]
        for _, pending_record in pending_records.iterrows():
            self.assertEqual(pending_record["linking_id"], pending_decision_id)
        non_pending_records = linked_data[linked_data["linking_id"] != pending_decision_id]
        self.assertEqual(len(non_pending_records), len(linked_data) - expected_dubious_matches)
