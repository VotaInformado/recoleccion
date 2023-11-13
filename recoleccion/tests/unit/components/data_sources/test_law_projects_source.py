from unittest import TestCase
from recoleccion.components.data_sources.law_projects_source import  (
    SenateLawProjectsSource
)


class SenateLawProjectsSourceTestCase(TestCase):
    def test_parse_deputies_project_id_gets_correctly(self):
        # Load content from file
        with open("recoleccion/tests/test_helpers/files/senate_project_details_200_CD_86.html", mode="rb") as f:
            content = f.read()

        id = SenateLawProjectsSource().get_deputies_project_id(content)

        self.assertEqual(id, "0043-PE-86")
