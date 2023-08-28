import random
from django.test import TestCase
from django.core.management import call_command
from recoleccion.components.data_sources.senate_source import SenateHistory, CurrentSenate
from recoleccion.models.authorship import Authorship
from recoleccion.models.law_project import LawProject
from recoleccion.models.person import Person


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
                law_project=law_project,
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
                law_project=project,
            )
        retrieved_person = Person.objects.get(pk=person.id)
        self.assertEqual(retrieved_person.law_projects.count(), PROJECTS_AMOUNT)
        person_projects = person.law_projects.all()
        for project in person_projects:
            self.assertIn(project, person_projects)
