# Django rest framework
from typing import List
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from django.db.models import Q, Count, Max

# Serializers
from recoleccion.serializers.authors import (
    AuthorsProjectsCountSerializer,
)
from recoleccion.serializers.law_projects import LawProjectListSerializer
from recoleccion.serializers.legislators import LegislatorDetailsSerializer
from recoleccion.serializers.parties import (
    PartyInfoSerializer,
    PartyDetailsSerializer,
    PartyVoteSessionSerializer,
)

# Models
from recoleccion.models import Party, Authorship, LawProject, Person
from recoleccion.utils.enums.vote_choices import VoteChoices
from recoleccion.utils.wrappers import manual_pagination


class PartiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Party.objects.all()

    ordering_fields = ["main_denomination"]
    search_fields = ["main_denomination"]

    def get_serializer_class(self):
        if self.action == "list":
            return PartyInfoSerializer
        elif self.action == "retrieve":
            return PartyDetailsSerializer

    @manual_pagination
    def list(self, request, *args, **kwargs):
        parties: List[Party] = list(self.get_queryset())
        parties.sort(key=lambda party: len(party.sub_parties), reverse=True)
        parties_data = self.get_serializer(parties, many=True).data
        return Response(parties_data)


class PartiesLawProjectVotesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = PartyVoteSessionSerializer

    search_fields = ["title"]
    ordering_fields = ["date"]
    ordering = ["-date"]

    def get_queryset(self):
        party_id = self.kwargs["party_id"]
        party = Party.objects.get(pk=party_id)
        party_projects = party.get_voted_projects()
        party_projects = party_projects.annotate(
            total_votes=Count("votes", filter=Q(votes__party=party)),
            date=Max("votes__date", filter=Q(votes__party=party)),
            afirmatives=Count(
                "votes",
                filter=Q(votes__party=party, votes__vote=VoteChoices.POSITIVE.value),
            ),
            negatives=Count(
                "votes",
                filter=Q(votes__party=party, votes__vote=VoteChoices.NEGATIVE.value),
            ),
            abstentions=Count(
                "votes",
                filter=Q(votes__party=party, votes__vote=VoteChoices.ABSTENTION.value),
            ),
            absents=Count(
                "votes",
                filter=Q(votes__party=party, votes__vote=VoteChoices.ABSENT.value),
            ),
        )
        return party_projects


class PartiesAuthorsProjectsCountViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = AuthorsProjectsCountSerializer

    # ordering_fields = [""]

    def get_queryset(self):
        party_id = self.kwargs["party_id"]
        authorships = (
            Person.objects.filter(authorships__party_id=party_id)
            .annotate(authorship_count=Count("authorships"))
            .order_by("-authorship_count")
        )
        return authorships


class PartiesLegislatorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LegislatorDetailsSerializer

    search_fields = ["name", "last_name"]
    filterset_fields = ["is_active", "last_seat"]
    ordering_fields = ["name", "last_name", "last_seat", "is_active"]

    def get_queryset(self):
        party_id = self.kwargs["party_id"]
        party = Party.objects.get(pk=party_id)
        members_ids = party.members_ids
        return Person.objects.filter(id__in=members_ids)


class PartiesLawProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LawProjectListSerializer

    search_fields = ["title"]
    ordering_fields = ["title", "publication_date", "status"]
    ordering = ["-publication_date"]
    filterset_fields = {
        "origin_chamber": ["exact"],
        "status": ["in"],
        "publication_date": ["gte", "lte"],
    }

    def get_queryset(self):
        party_id = self.kwargs["party_id"]
        project_ids = (
            Authorship.objects.filter(Q(party_id=party_id) & ~Q(project=None))
            .values_list("project", flat=True)
            .distinct()
        )
        projects = LawProject.objects.filter(id__in=project_ids).all()
        return projects
