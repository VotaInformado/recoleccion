from django.test import TestCase
from recoleccion.components.data_sources.senate_source import SenateHistory, CurrentSenate
from recoleccion.models.law_project import LawProject


class LawProjectNameTranslation(TestCase):
    def test_translating_name_from_format_1(self):
        original_id = "70-S-21"
        format_2_id = "70-S-2021"
        format_3_id = "0070-S-2021"
        format_4_id = "70-21"
        EXPECTED_IDS = [original_id, format_2_id, format_3_id, format_4_id]
        alternative_ids = LawProject.get_all_alternative_ids(original_id)
        self.assertEqual(alternative_ids, EXPECTED_IDS)

    def test_translating_name_from_format_2(self):
        original_id = "70-D-2021"
        format_1_id = "70-D-21"
        format_3_id = "0070-D-2021"
        format_4_id = "70-21"
        extra_format_1_id = "70-CD-21"
        extra_format_3_id = "0070-CD-2021"
        EXPECTED_IDS = [original_id, format_1_id, format_3_id, format_4_id, extra_format_1_id, extra_format_3_id]
        alternative_ids = LawProject.get_all_alternative_ids(original_id)
        self.assertEqual(alternative_ids, EXPECTED_IDS)

    def test_translating_name_from_format_3(self):
        original_id = "0009-D-2021"
        format_1_id = "9-D-21"
        format_2_id = "9-D-2021"
        format_4_id = "9-21"
        extra_format_1_id = "9-CD-21"
        extra_format_2_id = "9-CD-2021"
        EXPECTED_IDS = [original_id, format_1_id, format_2_id, format_4_id, extra_format_1_id, extra_format_2_id]
        alternative_ids = LawProject.get_all_alternative_ids(original_id)
        self.assertEqual(alternative_ids, EXPECTED_IDS)

    def test_translating_name_from_format_4(self):
        original_id = "9-21"
        format_1_ids = ["9-D-21", "9-S-21", "9-PE-21", "9-CD-21", "9-JMG-21", "9-OV-21"]
        format_2_ids = ["9-D-2021", "9-S-2021", "9-PE-2021", "9-CD-2021", "9-JMG-2021", "9-OV-2021"]
        format_3_ids = ["0009-D-2021", "0009-S-2021", "0009-PE-2021", "0009-CD-2021", "0009-JMG-2021", "0009-OV-2021"]
        EXPECTED_IDS = [original_id] + format_1_ids + format_2_ids + format_3_ids
        alternative_ids = LawProject.get_all_alternative_ids(original_id)
        self.assertEqual(sorted(alternative_ids), sorted(EXPECTED_IDS))
