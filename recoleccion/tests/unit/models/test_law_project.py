import random
from django.test import TestCase
from django.core.management import call_command
from recoleccion.components.services.text_summarizer import TextSummarizer

# Project
import recoleccion.tests.test_helpers.mocks as mck
from recoleccion.models.authorship import Authorship
from recoleccion.models.law_project import LawProject
from recoleccion.models.person import Person


class LawProjectAuthorsTestCase(TestCase):
    def test_retrieving_law_project_authors(self):
        AUTHORS_AMOUNT = 3
        call_command("loaddata", "recoleccion/fixtures/person.json")
        authors = []
        all_persons = list(Person.objects.all())
        for _ in range(AUTHORS_AMOUNT):
            random_author = random.choice(all_persons)
            all_persons.remove(random_author)
            authors.append(random_author)
        law_project = LawProject.objects.create(
            deputies_project_id="1-D-2021",
            title="Ley de presupuesto 2021",
            origin_chamber="Diputados",
            publication_date="2020-12-30",
            deputies_number=1,
            deputies_source="D",
            deputies_year=2021,
        )
        for author in authors:
            Authorship.objects.create(
                person=author,
                project=law_project,
            )
        retrieved_project: LawProject = LawProject.objects.get(pk=law_project.id)
        self.assertEqual(retrieved_project.authors.count(), AUTHORS_AMOUNT)
        law_project_authors = law_project.authors.all()
        for author in authors:
            self.assertIn(author, law_project_authors)

    def test_retrieving_person_law_projects(self):
        PROJECTS_AMOUNT = 2
        call_command("loaddata", "recoleccion/fixtures/law_project.json")
        person_projects = []
        all_projects = list(LawProject.objects.all())
        for _ in range(PROJECTS_AMOUNT):
            random_project = random.choice(all_projects)
            all_projects.remove(random_project)
            person_projects.append(random_project)
        person = Person.objects.create(
            name="Juan",
            last_name="Perez",
        )
        for project in person_projects:
            Authorship.objects.create(
                person=person,
                project=project,
            )
        retrieved_person = Person.objects.get(pk=person.id)
        self.assertEqual(retrieved_person.law_projects.count(), PROJECTS_AMOUNT)
        person_projects = person.law_projects.all()
        for project in person_projects:
            self.assertIn(project, person_projects)


class LawProjectSummarizationTestCase(TestCase):
    fixtures = ["law_project"]

    def test_correct_first_time_summarization(self):
        project = LawProject.objects.first()
        project.text = "Sólo necesitamos que no sea NULL"
        project.save()

        url = f"/law-projects/{project.id}/summary/"
        mocked_summary = "Resumen del proyecto"

        with mck.mock_method(TextSummarizer, "summarize_text", return_value=mocked_summary):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["summary"], mocked_summary)

    def test_correct_summary_retrieval_from_db(self):
        project = LawProject.objects.first()
        project.text = "Sólo necesitamos que no sea NULL"
        project.save()

        url = f"/law-projects/{project.id}/summary/"
        original_summary = "Resumen del proyecto"

        with mck.mock_method(TextSummarizer, "summarize_text", return_value=original_summary):
            response = self.client.get(url)

        different_summary = "Otro resumen"  # Should not be used

        with mck.mock_method(TextSummarizer, "summarize_text", return_value=different_summary) as mock:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["summary"], original_summary)
            mock.assert_not_called()

    def test_project_summary_cannot_be_done_when_project_has_no_text(self):
        project = LawProject.objects.first()
        project.text = random.choice([None, ""])
        project.save()

        url = f"/law-projects/{project.id}/summary/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
