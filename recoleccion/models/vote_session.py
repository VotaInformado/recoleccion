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
        # self.votes_summary = self.get_votes_summary(vote_list)

        self.afirmatives = self.votes.all().filter(vote=VoteChoices.POSITIVE.value).count()
        self.negatives = self.votes.all().filter(vote=VoteChoices.NEGATIVE.value).count()
        self.abstentions = self.votes.all().filter(vote=VoteChoices.ABSTENTION.value).count()
        self.absents = self.votes.all().filter(vote=VoteChoices.ABSENT.value).count()

    # def get_votes_summary(self, vote_list: List[Vote]):
    #     vote_choices = VoteChoices.choices
    #     summary = {}
    #     for value, label in [
    #         ("AFIRMATIVO", "afirmatives"),
    #         ("NEGATIVO", "negatives"),
    #         ("ABSTENCION", "abstentions"),
    #         ("AUSENTE", "absents"),
    #     ]:
    #         summary[label] = len(
    #             list(filter(lambda vote: vote.vote == value, vote_list))
    #         )
    #     return summary
