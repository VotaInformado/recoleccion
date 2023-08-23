# Django
from typing import List

# Project
from recoleccion.models.vote import Vote
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
        self.votes_summary = self.get_votes_summary(vote_list)

    def get_votes_summary(self, vote_list: List[Vote]):
        vote_choices = VoteChoices.choices
        summary = {}
        for value, label in vote_choices:
            summary[label] = len(list(filter(lambda vote: vote.vote == value, vote_list)))
        return summary
