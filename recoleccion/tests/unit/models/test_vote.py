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
