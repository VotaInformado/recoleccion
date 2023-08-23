import random

# Project
from recoleccion.models.law_project import LawProject
from recoleccion.models.vote import Vote
from recoleccion.tests.test_helpers.test_case import LinkingAPITestCase
from recoleccion.models.person import Person
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_choices import VoteChoices


class LegislatorViewTestCase(LinkingAPITestCase):
    fixtures = ["person.json", "law_project.json"]

    def create_votes(self, total_votes, law_project, date, chamber):
        self.persons = Person.objects.all()[:total_votes]
        for i in range(total_votes):
            Vote.objects.create(
                chamber=chamber,
                date=date,
                person=self.persons[i],
                project=law_project,
                vote=random.choice(VoteChoices.values),
            )

    def setUp(self):
        self.law_project = LawProject.objects.first()

    def test_law_project_retrieval(self):
        EXPECTED_DEPUTIES_VOTES = 10
        EXPECTED_SENATORS_VOTES = 12
        DEPUTIES_VOTE_DATE = "2020-01-01"
        SENATORS_VOTE_DATE = "2020-01-02"
        self.create_votes(EXPECTED_DEPUTIES_VOTES, self.law_project, DEPUTIES_VOTE_DATE, ProjectChambers.DEPUTIES)
        self.create_votes(EXPECTED_SENATORS_VOTES, self.law_project, SENATORS_VOTE_DATE, ProjectChambers.SENATORS)
        url = f"/law-projects/{self.law_project.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        senate_vote_session = response.json()["senate_vote_session"]
        deputies_vote_session = response.json()["deputies_vote_session"]
        self.assertEqual(senate_vote_session["chamber"], ProjectChambers.SENATORS)
        self.assertEqual(senate_vote_session["date"], SENATORS_VOTE_DATE)
        self.assertEqual(len(senate_vote_session["votes"]), EXPECTED_SENATORS_VOTES)
        self.assertEqual(deputies_vote_session["chamber"], ProjectChambers.DEPUTIES)
        self.assertEqual(deputies_vote_session["date"], DEPUTIES_VOTE_DATE)
        self.assertEqual(len(deputies_vote_session["votes"]), EXPECTED_DEPUTIES_VOTES)

    def test_law_project_list(self):
        url = "/law-projects/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        total_projects = LawProject.objects.count()
        self.assertEqual(len(response.json()), total_projects)
