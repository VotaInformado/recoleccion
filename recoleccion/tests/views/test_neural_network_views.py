import random
from datetime import datetime, timedelta
from django.core.management import call_command
from django.db import transaction
from rest_framework.test import APITestCase
import random
from tqdm import tqdm
import pandas as pd
import numpy as np

# Project
from recoleccion.models import Authorship, LawProject, Party, Person, Vote
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_choices import VoteChoices


class NeuralNetworkDataTestCase(APITestCase):
    fixtures = ["person", "partydenomination", "party", "law_project"]

    def create_votes(self, votes_per_project):
        date = "2020-01-02"
        chamber = ProjectChambers.DEPUTIES
        law_projects = LawProject.objects.all()
        persons = Person.objects.all()[:votes_per_project]
        for project in tqdm(law_projects):
            for i in range(votes_per_project):
                Vote.objects.create(
                    chamber=chamber,
                    date=date,
                    person=persons[i],
                    project=project,
                    vote=random.choice(VoteChoices.values),
                )

    def create_authors(self, authors_per_project):
        law_projects = LawProject.objects.all()
        persons = Person.objects.all()[:authors_per_project]
        partys = Party.objects.all()[:authors_per_project]
        for project in tqdm(law_projects):
            for i in range(authors_per_project):
                Authorship.objects.create(
                    project=project, person=persons[i], party=partys[i], author_type=LegislatorSeats.DEPUTY
                )

    def create_law_projects(self, amount: int):
        publication_date = datetime.now()
        for _ in range(amount):
            LawProject.objects.create(
                origin_chamber=ProjectChambers.DEPUTIES,
                title="A title",
                text="Some text",
                publication_date=publication_date,
            )

    def test_retrieving_all_votes_for_neural_network(self):
        PAGE_SIZE = 1000
        VOTES_PER_PROJECT = 3
        EXPECTED_COLUMNS = {
            "vote": str,
            "date": str,
            "person": int | np.integer,
            "party": int | np.integer,
            "project": int | np.integer,
        }
        total_projects = LawProject.objects.count()
        self.create_votes(votes_per_project=VOTES_PER_PROJECT)  # Total: 3 * 1000 = 3000 votes
        received_data = []
        url = "/neural-network/votes/"
        params = {"page_size": PAGE_SIZE}
        while True:
            response = self.client.get(url, data=params)
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break
        df = pd.DataFrame(received_data)
        self.assertEqual(len(df), total_projects * VOTES_PER_PROJECT)
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        sample_row = df.iloc[0]
        for column, dtype in EXPECTED_COLUMNS.items():
            value = sample_row[column]
            self.assertTrue(value is None or isinstance(value, dtype))

    def test_retrieveing_votes_for_neural_network_with_filter(self):
        PAGE_SIZE = 1000
        NEW_VOTES = 2000  # Page size is 1000 by default
        VOTES_PER_PROJECT = 3
        EXPECTED_COLUMNS = {
            "vote": str,
            "date": str,
            "person": int | np.integer,
            "party": int | np.integer,
            "project": int | np.integer,
        }
        self.create_votes(VOTES_PER_PROJECT)  # Total: 3 * 1000 = 3000 votes
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        all_votes = list(Vote.objects.all())
        new_votes = all_votes[:NEW_VOTES]
        old_votes = all_votes[NEW_VOTES:]

        for author in new_votes:
            author.created_at = now
            author.save()
        for author in old_votes:
            author.created_at = yesterday
            author.save()

        new_votes = Vote.objects.filter(created_at__gte=now)
        received_data = []
        params = {
            "page_size": PAGE_SIZE,
            "created_at__gte": now,
        }
        url = "/neural-network/votes/"

        while True:
            print("url: ", url)
            response = self.client.get(url, data=params)
            self.assertEqual(response.status_code, 200, response.json())
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break

        df = pd.DataFrame(received_data)
        self.assertEqual(len(df), len(new_votes))
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        sample_row = df.iloc[0]
        for column, dtype in EXPECTED_COLUMNS.items():
            value = sample_row[column]
            self.assertTrue(value is None or isinstance(value, dtype))

    def test_retrieving_all_authors_for_neural_network(self):
        PAGE_SIZE = 1000
        AUTHORS_PER_PROJECT = 3
        EXPECTED_COLUMNS = {
            "party": int | np.integer,
            "person": int | np.integer,
            "project": int | np.integer,
        }
        total_projects = LawProject.objects.count()
        self.create_authors(AUTHORS_PER_PROJECT)  # Total: 3 * 1000 = 3000 votes
        received_data = []
        params = {"page_size": PAGE_SIZE}
        url = "/neural-network/authors/"
        while True:
            response = self.client.get(url, data=params)
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break
        df = pd.DataFrame(received_data)
        self.assertEqual(len(df), total_projects * AUTHORS_PER_PROJECT)
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        sample_row = df.iloc[0]
        for column, dtype in EXPECTED_COLUMNS.items():
            value = sample_row[column]
            self.assertTrue(value is None or isinstance(value, dtype))

    def test_retrieveing_authors_for_neural_network_with_filter(self):
        PAGE_SIZE = 1000
        NEW_AUTHORS = 2000  # Page size is 1000 by default
        AUTHORS_PER_PROJECT = 3
        EXPECTED_COLUMNS = {
            "party": int | np.integer,
            "person": int | np.integer,
            "project": int | np.integer,
        }
        self.create_authors(AUTHORS_PER_PROJECT)  # Total: 3 * 1000 = 3000 votes
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        all_authors = list(Authorship.objects.all())
        new_authors = all_authors[:NEW_AUTHORS]
        old_authors = all_authors[NEW_AUTHORS:]

        for author in new_authors:
            author.created_at = now
            author.save()
        for author in old_authors:
            author.created_at = yesterday
            author.save()

        new_authors = Authorship.objects.filter(created_at__gte=now)
        received_data = []
        params = {
            "page_size": PAGE_SIZE,
            "created_at__gte": now,
        }
        url = "/neural-network/authors/"

        while True:
            print("url: ", url)
            response = self.client.get(url, data=params)
            self.assertEqual(response.status_code, 200, response.json())
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break

        df = pd.DataFrame(received_data)
        self.assertEqual(len(df), len(new_authors))
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        sample_row = df.iloc[0]
        for column, dtype in EXPECTED_COLUMNS.items():
            value = sample_row[column]
            self.assertTrue(value is None or isinstance(value, dtype))

    def test_retrieving_all_projects_for_neural_network(self):
        PAGE_SIZE = 1000
        EXPECTED_COLUMNS = {
            "project_id": str,
            "project_title": str,
            "project_text": str,
            "project_year": int | np.integer,
        }
        total_projects = LawProject.objects.count()
        received_data = []
        params = {"page_size": PAGE_SIZE}
        url = "/neural-network/law-projects/"
        while True:
            response = self.client.get(url, data=params)
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break
        df = pd.DataFrame(received_data)
        self.assertEqual(len(df), total_projects)
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        sample_row = df.iloc[0]
        for column, dtype in EXPECTED_COLUMNS.items():
            value = sample_row[column]
            self.assertTrue(value is None or isinstance(value, dtype))

    def test_retrieving_projects_for_neural_network_with_filter(self):
        PAGE_SIZE = 1000
        TOTAL_PROJECTS = 3000
        NEW_PROJECTS = 2000  # Page size is 1000 by default
        EXPECTED_COLUMNS = {
            "project_id": str,
            "project_title": str,
            "project_text": str,
            "project_year": int | np.integer,
        }
        # delete all projects
        LawProject.objects.all().delete()
        self.create_law_projects(amount=TOTAL_PROJECTS)
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        new_law_projects = list(LawProject.objects.all())[:NEW_PROJECTS]
        old_law_projects = list(LawProject.objects.all())[NEW_PROJECTS:]
        for project in new_law_projects:
            project.created_at = now
            project.save()
        for project in old_law_projects:
            project.created_at = yesterday
            project.save()
        new_projects = LawProject.objects.filter(created_at__gte=now)
        self.assertEqual(len(new_projects), NEW_PROJECTS)
        received_data = []
        url = "/neural-network/law-projects/"
        params = {"created_at__gte": now, "page_size": PAGE_SIZE}
        while True:
            print("url: ", url)
            response = self.client.get(url, data=params)
            self.assertEqual(response.status_code, 200, response.json())
            response_results = response.json()["results"]
            received_data.extend(response_results)
            url = response.json()["next"]
            params = None  # Si no se pisan, se overridean params de la url y queda en un loop infinito
            if url is None:
                break
        df = pd.DataFrame(received_data)
        self.assertEqual(set(df.columns), set(EXPECTED_COLUMNS.keys()))
        self.assertEqual(len(df), len(new_projects))
