from django.test import TestCase
from recoleccion.models import LawProject
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter


class LawsProjectWriter(TestCase):
    def test_update_or_create_when_field_is_not_updated(self):
        PROJECT_ID = "2345-D-2019"
        ORIGINAL_PUBLICATION_DATE = "2020-12-30"
        deputies_number, deputies_source, deputies_year = LawProjectsWriter.split_id(PROJECT_ID)
        existing_project = LawProject.objects.create(
            deputies_project_id=PROJECT_ID,
            title="Ley de presupuesto 2021",
            origin_chamber="Diputados",
            publication_date=ORIGINAL_PUBLICATION_DATE,
            deputies_number=deputies_number,
            deputies_source=deputies_source,
            deputies_year=deputies_year,
        )
        new_project_data = {
            "deputies_project_id": PROJECT_ID,
            "title": "Ley de presupuesto 2021",
            "origin_chamber": "Diputados",
        }
        LawProject.objects.update_or_create(
            deputies_number=deputies_number,  # the writer does not use the id anymore
            deputies_year=deputies_year,
            defaults=new_project_data,
        )
        law_project = LawProject.objects.get(deputies_project_id=PROJECT_ID)
        project_date_str = law_project.publication_date.strftime("%Y-%m-%d")
        self.assertEqual(project_date_str, ORIGINAL_PUBLICATION_DATE)

    def test_update_or_create_when_field_updated_with_null_value(self):
        PROJECT_ID = "2345-D-2019"
        deputies_number, deputies_source, deputies_year = LawProjectsWriter.split_id(PROJECT_ID)
        ORIGINAL_PUBLICATION_DATE = "2020-12-30"
        existing_project = LawProject.objects.create(
            deputies_project_id=PROJECT_ID,
            title="Ley de presupuesto 2021",
            origin_chamber="Diputados",
            publication_date=ORIGINAL_PUBLICATION_DATE,
            deputies_number=deputies_number,
            deputies_source=deputies_source,
            deputies_year=deputies_year,
        )
        new_project_data = {
            "deputies_project_id": PROJECT_ID,
            "title": "Ley de presupuesto 2021",
            "origin_chamber": "Diputados",
            "publication_date": None,
            "deputies_number": deputies_number,
            "deputies_year": deputies_year,
        }
        LawProject.objects.update_or_create(
            deputies_number=deputies_number,  # the writer does not use the id anymore
            deputies_year=deputies_year,
            defaults=new_project_data,
        )
        law_project = LawProject.objects.get(deputies_project_id=PROJECT_ID)
        self.assertEqual(law_project.publication_date, None)
