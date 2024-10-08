# Django
from typing import List
from django.db import models

# Project
from recoleccion.models.base import BaseModel
from recoleccion.models.authorship import Authorship
from recoleccion.models.deputy_seat import DeputySeat
from recoleccion.models.law_project import LawProject
from recoleccion.models.person import Person
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.models.vote import Vote
from recoleccion.utils.enums.party_relation_types import PartyRelationTypes


class Party(BaseModel):
    main_denomination = models.CharField(max_length=200, unique=True, null=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # it's a new object
            super().save(*args, **kwargs)
            PartyDenomination.objects.create(
                party=self,
                denomination=self.main_denomination,
                relation_type=PartyRelationTypes.ALTERNATIVE_DENOMINATION,
            )
        else:
            super().save(*args, **kwargs)

    @property
    def alternative_denominations(self) -> List[str]:
        main_denomination = PartyDenomination.objects.filter(denomination=self.main_denomination).first()
        if not main_denomination:
            main_denomination_id = None
        else:
            main_denomination_id = main_denomination.pk
        all_denominations = PartyDenomination.objects.filter(
            party=self, relation_type=PartyRelationTypes.ALTERNATIVE_DENOMINATION
        ).exclude(id=main_denomination_id)
        return [denomination.denomination for denomination in all_denominations]

    @property
    def sub_parties(self) -> List[str]:
        sub_parties = PartyDenomination.objects.filter(party=self, relation_type=PartyRelationTypes.SUB_PARTY)
        return [sub_party.denomination for sub_party in sub_parties]

    @property
    def members(self) -> List[Person]:
        deputy_members = DeputySeat.objects.filter(party=self).values_list("person", flat=True)
        senate_members = SenateSeat.objects.filter(party=self).values_list("person", flat=True)
        members_from_votes = Vote.objects.filter(party=self).values_list("person", flat=True)
        members_from_authors = Authorship.objects.filter(party=self).values_list("person", flat=True)
        members = list(deputy_members) + list(senate_members) + list(members_from_votes) + list(members_from_authors)
        members = set(members)
        return [Person.objects.get(pk=member_id) for member_id in members if member_id]

    @property
    def members_ids(self) -> List[int]:
        deputy_seats = self.deputy_seats.values("person_id").distinct()
        senate_seats = self.senate_seats.values("person_id").distinct()
        votes = self.votes.values("person_id").distinct()
        authorships = self.authorships.values("person_id").distinct()
        return deputy_seats.union(senate_seats, votes, authorships)

    @property
    def law_projects(self) -> List[LawProject]:
        project_ids = Authorship.objects.filter(party=self).values_list("project", flat=True).distinct()
        law_projects = [LawProject.objects.get(pk=project_id) for project_id in project_ids if project_id]
        return law_projects

    def get_voted_projects(self) -> List[LawProject]:
        law_projects = LawProject.objects.filter(votes__party=self).distinct().order_by("-id")
        return law_projects

    @property
    def votes(self) -> List[Vote]:
        return Vote.objects.filter(party=self)

    def get_project_votes(self, project: LawProject):
        return Vote.objects.filter(project=project, party=self)


class PartyDenomination(BaseModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="denominations")
    denomination = models.CharField(max_length=200, unique=True)
    relation_type = models.CharField(
        max_length=50,
        choices=PartyRelationTypes.choices,
        default=PartyRelationTypes.ALTERNATIVE_DENOMINATION,
    )
