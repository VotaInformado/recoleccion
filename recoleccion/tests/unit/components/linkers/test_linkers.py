from django.conf import settings
from dedupe import Gazetteer

# Project

import recoleccion.tests.test_helpers.utils as ut
from recoleccion.components.linkers import PartyLinker, PersonLinker
from recoleccion.models.linking.person_linking import PersonLinkingDecision
from recoleccion.models.party import Party
from recoleccion.models.person import Person
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.tests.test_helpers.faker import create_fake_df
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


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
            "full_name": "str",
            "id": "int",
        }

    def create_person_linking_decision(self, messy_name: str, canonical_name: str, decision: str, person_id=1):
        person_id = person_id if decision != LinkingDecisionOptions.DENIED else None
        PersonLinkingDecision.objects.create(messy_name=messy_name, decision=decision, person_id=person_id)

    def test_senator_linking_with_repeated_records(self):
        EXPECTED_ID = 1
        WRONG_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan C",
            "last_name": "Perez",
            "person_id": WRONG_ID,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Juan C"]
        self.assertEqual(row["person_id"].values[0], EXPECTED_ID)

    def test_senator_linking_without_repeated_records(self):
        # Two different persons should not be merged
        WRONG_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": WRONG_ID,
        }
        updated_record = {
            "name": "Eustaquio",
            "last_name": "Quintero",
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Eustaquio"]
        id_value = row["person_id"].values[0]
        self.assertIsNone(id_value)

    def test_senator_linking_same_last_name_should_not_be_enough(self):
        # Two persons with different names but same last name should not be merged
        WRONG_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": WRONG_ID,
        }
        updated_record = {
            "name": "Eustaquio",
            "last_name": "Perez",
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Eustaquio"]
        id_value = row["person_id"].values[0]
        self.assertIsNone(id_value)

    def test_senator_linking_with_different_second_name(self):
        EXPECTED_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan Eustaquio",
            "last_name": "Perez",
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Juan Eustaquio"]
        id_value = row["person_id"].values[0]
        self.assertEqual(id_value, EXPECTED_ID)

    def test_senator_linking_special_case_1(self):
        # Different second name and last name has different accentuation
        EXPECTED_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan Eustaquio",
            "last_name": "Pérez",
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Juan Eustaquio"]
        id_value = row["person_id"].values[0]
        self.assertEqual(id_value, EXPECTED_ID)

    def test_senator_linking_special_case_2(self):
        # One person's second name is the other person's first name
        WRONG_ID = 2

        canonical_record = {
            "full_name": "Perez Juan",
            "id": WRONG_ID,
        }
        updated_record = {
            "name": "Roberto Juan",
            "last_name": "Perez",
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Roberto Juan"]
        id_value = row["person_id"].values[0]
        self.assertIsNone(id_value)

    def test_person_linking_with_repeated_records_but_previous_denied_linking(self):
        """
        Hierarchy:
        1. Exact matching (this case) X -> This should be the final decision (same record)
        2. Previous decisions
        3. Gazetteer
        """

        person = Person.objects.create(name="Juan", last_name="Perez")
        EXPECTED_ID = person.pk
        WRONG_ID = person.pk + 1
        MESSY_FULL_NAME = CANONICAL_FULL_NAME = "Juan Perez"
        self.create_person_linking_decision(MESSY_FULL_NAME, CANONICAL_FULL_NAME, LinkingDecisionOptions.DENIED)

        canonical_record = {
            "full_name": "Perez Juan",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan",
            "last_name": "Perez",
            "person_id": WRONG_ID,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Juan"]
        id_value = row["person_id"].values[0]
        self.assertEqual(id_value, EXPECTED_ID)

    def test_person_linking_with_different_records_but_previous_approved_linking(self):
        # Even if the records are different, if there is a previous approved linking, the records should be merged
        WRONG_ID = 2
        MESSY_FULL_NAME = "Roberto Clodomiro Paletta"
        CANONICAL_FULL_NAME = "Juan Perez"
        person = Person.objects.create(name="Juan", last_name="Perez")
        EXPECTED_ID = person.pk

        self.create_person_linking_decision(
            MESSY_FULL_NAME, CANONICAL_FULL_NAME, LinkingDecisionOptions.APPROVED, person_id=person.pk
        )

        canonical_record = {
            "full_name": "Perez Juan",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan",
            "last_name": "Perez",
            "person_id": WRONG_ID,
            "province": "Córdoba",
            "start_of_term": "2019-01-10",
            "end_of_term": "2023-01-02",
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PersonLinker, "get_canonical_data", return_value=canonical_data):
            linker = PersonLinker()
            linked_data = linker.link_persons(updated_data)
        row = linked_data[linked_data["name"] == "Juan"]
        id_value = row["person_id"].values[0]
        self.assertEqual(id_value, EXPECTED_ID)


class PartyLinkerTestCase(LinkingTestCase):
    def setUp(self):
        self.messy_columns = {
            "denomination": "party",
            "record_id": "int",
        }
        self.canonical_columns = {
            "denomination": "party",
            "party_id": "int",
        }

    def test_party_linking_with_repeated_records(self):
        EXPECTED_ID = 1
        RECORD_ID = 2
        DENOMINATION = "Partido Justicialista"

        canonical_record = {
            "denomination": DENOMINATION,
            "party_id": EXPECTED_ID,
        }
        updated_record = {
            "denomination": DENOMINATION,
            "record_id": RECORD_ID,
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PartyLinker, "get_canonical_data", return_value=canonical_data):
            linker = PartyLinker()
            linked_data = linker.link_parties(updated_data)
        row = linked_data[linked_data["denomination"] == DENOMINATION]
        self.assertEqual(row["record_id"].values[0], RECORD_ID)
        self.assertEqual(row["party_id"].values[0], EXPECTED_ID)

    def test_party_linking_with_similar_records_and_no_previous_decision(self):
        EXPECTED_ID = 1
        RECORD_ID = 2
        CANONICAL_DENOMINATION = "Partido Justicialista"
        MESSY_DENOMINATION = "Part. Justicialista"

        canonical_record = {
            "denomination": CANONICAL_DENOMINATION,
            "party_id": EXPECTED_ID,
        }
        updated_record = {
            "denomination": MESSY_DENOMINATION,
            "record_id": RECORD_ID,
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PartyLinker, "get_canonical_data", return_value=canonical_data):
            linker = PartyLinker()
            linked_data = linker.link_parties(updated_data)
        row = linked_data[linked_data["denomination"] == MESSY_DENOMINATION]
        self.assertEqual(row["record_id"].values[0], RECORD_ID)
        self.assertEqual(row["party_id"].values[0], EXPECTED_ID)

    def test_party_linking_with_similar_records_and_previous_approved_linking(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Previous decisions  X -> This should be the final decision (same record)
        3. Gazetteer
        """

        RECORD_ID = 2
        CANONICAL_DENOMINATION = "Partido Justicialista"
        MESSY_DENOMINATION = "Part. Justicialista"
        party = Party.objects.create(main_denomination=CANONICAL_DENOMINATION)
        EXPECTED_ID = party.pk
        ut.create_party_linking_decision(
            MESSY_DENOMINATION, CANONICAL_DENOMINATION, LinkingDecisionOptions.APPROVED, party.pk
        )

        canonical_record = {
            "denomination": CANONICAL_DENOMINATION,
            "party_id": EXPECTED_ID,
        }
        updated_record = {
            "denomination": MESSY_DENOMINATION,
            "record_id": RECORD_ID,
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PartyLinker, "get_canonical_data", return_value=canonical_data):
            linker = PartyLinker()
            linked_data = linker.link_parties(updated_data)
        row = linked_data[linked_data["denomination"] == MESSY_DENOMINATION]
        self.assertEqual(row["record_id"].values[0], RECORD_ID)
        self.assertEqual(row["party_id"].values[0], EXPECTED_ID)

    def test_party_linking_with_repeated_records_but_previous_denied_linking(self):
        """
        Hierarchy:
        1. Exact matching (this case) X -> This should be the final decision (same record)
        2. Previous decisions
        3. Gazetteer
        """
        RECORD_ID = 2
        DENOMINATION = "Partido Justicialista"
        ut.create_party_linking_decision(DENOMINATION, DENOMINATION, LinkingDecisionOptions.DENIED)
        party = Party.objects.create(main_denomination=DENOMINATION)
        PARTY_ID = party.pk

        canonical_record = {
            "denomination": DENOMINATION,
            "party_id": PARTY_ID,
        }
        updated_record = {
            "denomination": DENOMINATION,
            "record_id": RECORD_ID,
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_data[len(canonical_data) + 1] = canonical_record
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        updated_data.loc[len(updated_data)] = updated_record
        with mck.mock_method(PartyLinker, "get_canonical_data", return_value=canonical_data):
            linker = PartyLinker()
            linked_data = linker.link_parties(updated_data)
        row = linked_data[linked_data["denomination"] == DENOMINATION]
        self.assertEqual(row["record_id"].values[0], RECORD_ID)
        self.assertEqual(row["party_id"].values[0], PARTY_ID)

    def test_party_linking_with_different_records_but_previous_approved_decision(self):
        """
        Hierarchy:
        1. Exact matching (this case)
        2. Gazetteer
        3. Previous decisions (dubious records only)  X -> This should be the final decision (different record)
        """
        RECORD_ID = 2
        settings.REAL_METHOD = Gazetteer.search
        CANONICAL_DENOMINATION = "DIFFERENT_PARTY"
        MESSY_DENOMINATION = "Partido Justicialista"
        party = Party.objects.create(main_denomination=CANONICAL_DENOMINATION)
        EXPECTED_ID = party.pk
        ut.create_party_linking_decision(
            MESSY_DENOMINATION, CANONICAL_DENOMINATION, LinkingDecisionOptions.APPROVED, party.pk
        )
        canonical_record = {
            "denomination": CANONICAL_DENOMINATION,
            "party_id": EXPECTED_ID,
        }
        updated_record = {
            "denomination": MESSY_DENOMINATION,
            "record_id": RECORD_ID,
        }

        canonical_data: dict = create_fake_df(self.canonical_columns, n=10)
        canonical_index = len(canonical_data) + 1
        canonical_data[canonical_index] = canonical_record
        settings.CANONICAL_INDEXES = [canonical_index]
        updated_data = create_fake_df(self.messy_columns, n=8, as_dict=False, dates_as_str=False)
        messy_index = len(updated_data)
        updated_data.loc[messy_index] = updated_record
        settings.MESSY_INDEXES = [messy_index]  # these are the indexes of the pending decisions messy records
        with mck.mock_method(PartyLinker, "get_canonical_data", return_value=canonical_data):
            with mck.mock_method_side_effect(Gazetteer, "search", side_effect=mck.mock_linking_results):
                linker = PartyLinker()
                linked_data = linker.link_parties(updated_data)
            row = linked_data[linked_data["denomination"] == MESSY_DENOMINATION]
        self.assertEqual(row["record_id"].values[0], RECORD_ID)
        self.assertEqual(row["party_id"].values[0], EXPECTED_ID)
