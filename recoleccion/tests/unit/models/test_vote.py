from django.db import IntegrityError
from django.test import TestCase
from recoleccion.components.data_sources.senate_source import SenateHistory, CurrentSenate
from recoleccion.models.law_project import LawProject
from recoleccion.models.person import Person
from recoleccion.models.vote import Vote


class VoteConstraint(TestCase):
    fixtures = ["person.json", "law_project.json"]

    def test_vote_constraint_works(self):
        law_project = LawProject.objects.first()
        person = Person.objects.first()
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        Vote.objects.create(chamber=chamber, date=date, person=person, project=law_project, vote=vote)
        with self.assertRaises(IntegrityError):
            Vote.objects.create(chamber=chamber, date=date, person=person, project=law_project, vote=vote)

    def test_vote_constraint_works_in_a_loop(self):
        law_project = LawProject.objects.first()
        person = Person.objects.first()
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        for i in range(10):
            if i == 0:
                Vote.objects.create(chamber=chamber, date=date, person=person, project=law_project, vote=vote)
            else:
                with self.assertRaises(IntegrityError):
                    Vote.objects.create(chamber=chamber, date=date, person=person, project=law_project, vote=vote)

    def test_vote_constraint_works_when_reference_is_null(self):
        law_project = LawProject.objects.first()
        person = Person.objects.first()
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        Vote.objects.create(chamber=chamber, date=date, person=person, project=law_project, vote=vote, reference=None)
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                chamber=chamber, date=date, person=person, project=law_project, vote=vote, reference=None
            )

    def test_vote_constraint_has_no_effect_when_project_law_and_reference_are_null(self):
        law_project = LawProject.objects.first()
        person = Person.objects.first()
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        Vote.objects.create(
            chamber=chamber, date=date, person=person, project=None, law=None, reference=None, vote=vote
        )
        Vote.objects.create(
            chamber=chamber, date=date, person=person, project=None, law=None, reference=None, vote=vote
        )
        self.assertEqual(Vote.objects.count(), 2)

    def test_vote_constraint_uses_name_and_last_name_when_person_is_null(self):
        law_project = LawProject.objects.first()
        person = Person.objects.first()
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        Vote.objects.create(
            chamber=chamber,
            date=date,
            person=None,
            project=law_project,
            person_name=person.name,
            person_last_name=person.last_name,
            vote=vote,
        )
        with self.assertRaises(IntegrityError):
            Vote.objects.create(
                chamber=chamber,
                date=date,
                person=None,
                project=law_project,
                person_name=person.name,
                person_last_name=person.last_name,
                vote=vote,
            )


class VoteBulkOperations(TestCase):
    fixtures = ["person.json", "law_project.json"]

    def _create_votes(self, total_votes=10):
        law_projects = LawProject.objects.all()[:10]
        persons = Person.objects.all()[:10]
        chamber = "SENATORS"
        date = "2020-01-01"
        vote = "POSITIVE"
        votes = []
        for i in range(total_votes):
            person = persons[i]
            votes.append(
                Vote(
                    chamber=chamber,
                    date=date,
                    person=person,
                    project=law_projects[i],
                    person_name=person.name,
                    person_last_name=person.last_name,
                    vote=vote,
                )
            )
        return votes

    def test_vote_bulk_creation(self):
        TOTAL_VOTES = 10
        self.assertEqual(Vote.objects.count(), 0)
        votes = self._create_votes(TOTAL_VOTES)
        Vote.objects.bulk_create(votes)
        self.assertEqual(Vote.objects.count(), TOTAL_VOTES)

    def test_vote_bulk_update(self):
        TOTAL_VOTES = 10
        self.assertEqual(Vote.objects.count(), 0)
        votes = self._create_votes(TOTAL_VOTES)
        Vote.objects.bulk_create(votes)
        self.assertEqual(Vote.objects.count(), TOTAL_VOTES)
        for vote in votes:
            vote.vote = "NEGATIVE"
        Vote.objects.bulk_update(votes, ["vote"])
        self.assertEqual(Vote.objects.filter(vote="NEGATIVE").count(), TOTAL_VOTES)
        self.assertEqual(Vote.objects.filter(vote="POSITIVE").count(), 0)
