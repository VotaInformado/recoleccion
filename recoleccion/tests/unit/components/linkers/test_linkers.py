from django.core.management import call_command

# Project
from recoleccion.components.linkers import PersonLinker
from recoleccion.tests.test_helpers.test_case import LinkingTestCase
from recoleccion.tests.test_helpers.faker import create_fake_df
import recoleccion.tests.test_helpers.mocks as mck


class LinkingTestCase(LinkingTestCase):
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

    def test_senator_linking_with_repeated_records(self):
        EXPECTED_ID = 1
        WRONG_ID = 2

        canonical_record = {
            "name": "Juan",
            "last_name": "Perez",
            "id": EXPECTED_ID,
        }
        updated_record = {
            "name": "Juan C.",
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
        row = linked_data[linked_data["name"] == "Juan C."]
        self.assertEqual(row["person_id"].values[0], EXPECTED_ID)

    def test_senator_linking_without_repeated_records(self):
        # Two different persons should not be merged
        WRONG_ID = 2

        canonical_record = {
            "name": "Juan",
            "last_name": "Perez",
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
            "name": "Juan",
            "last_name": "Perez",
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
            "name": "Juan",
            "last_name": "Perez",
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
            "name": "Juan",
            "last_name": "Perez",
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
            "name": "Juan",
            "last_name": "Perez",
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
