# Django
from typing import List

# Project
from recoleccion.models.vote import Vote
from recoleccion.models.law_project import LawProject
from recoleccion.utils.enums.vote_choices import VoteChoices


class VoteSession:
    def __init__(self, vote_list: List[Vote]):
        chamber = vote_list[0].chamber
        if any(vote.chamber != chamber for vote in vote_list):
            raise ValueError("All votes must be from the same chamber")
        self.chamber = chamber
        date = vote_list[0].date
        self.date = date
        self.votes = vote_list

        self.afirmatives = (
            self.votes.all().filter(vote=VoteChoices.POSITIVE.value).count()
        )
        self.negatives = (
            self.votes.all().filter(vote=VoteChoices.NEGATIVE.value).count()
        )
        self.abstentions = (
            self.votes.all().filter(vote=VoteChoices.ABSTENTION.value).count()
        )
        self.absents = self.votes.all().filter(vote=VoteChoices.ABSENT.value).count()


class PartyVoteSession:
    from recoleccion.models.party import Party

    def __init__(self, law_project: LawProject):
        self.project_title = law_project.title
        self.date = law_project.date

        self.afirmatives = law_project.afirmatives
        self.negatives = law_project.negatives
        self.abstentions = law_project.abstentions
        self.absents = law_project.absents
        self.total_votes = law_project.total_votes
