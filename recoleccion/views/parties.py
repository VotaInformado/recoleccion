# Django rest framework
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q, Count, Max

from recoleccion.views.paginator import StandardResultsSetPagination

# Serializers
from recoleccion.serializers.authors import (
    AuthorshipModelSerializer,
    AuthorsProjectsCountSerializer,
)
from recoleccion.serializers.law_projects import LawProjectListSerializer
from recoleccion.serializers.parties import (
    PartyInfoSerializer,
    PartyDetailsSerializer,
    PartyVoteSessionSerializer,
    PartyVotesRequestSerializer,
)
from recoleccion.models import PartyVoteSession

# Models
from recoleccion.models import Party, Authorship, LawProject, Person
from recoleccion.utils.enums.vote_choices import VoteChoices


class PartiesViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    queryset = Party.objects.all()

    ordering_fields = ["main_denomination"]
    search_fields = ["main_denomination"]

    def get_serializer_class(self):
        if self.action == "list":
            return PartyInfoSerializer
        elif self.action == "retrieve":
            return PartyDetailsSerializer
        elif self.action == "get_party_votes":
            return PartyVoteSessionSerializer

    def _get_party_votes_per_project(self, party: Party):
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
        ).order_by("-date")
        return party_projects

    @swagger_auto_schema(
        methods=["get"],
        query_serializer=PartyVotesRequestSerializer,
        responses=[],
        operation_description="Retrieves the party votes for each law project where the party voted",
    )
    @action(detail=True, methods=["get"], url_path="votes")
    def get_party_votes(self, request, pk=None):
        serializer = PartyVotesRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        party: Party = self.get_object()
        vote_session_data = self._get_party_votes_per_project(party)
        page = self.paginate_queryset(vote_session_data)
        if page is None:
            serializer = PartyVoteSessionSerializer(vote_session_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        paginator = StandardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(vote_session_data, request)
        serializer = PartyVoteSessionSerializer(paginated_data, many=True)
        return self.get_paginated_response(serializer.data)


class PartiesAuthorsProjectsCountViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin
):
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


class PartiesLawProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LawProjectListSerializer

    # ordering_fields = [""]

    def get_queryset(self):
        party_id = self.kwargs["party_id"]
        project_ids = (
            Authorship.objects.filter(Q(party_id=party_id) & ~Q(project=None))
            .values_list("project", flat=True)
            .distinct()
        )
        projects = LawProject.objects.filter(id__in=project_ids).all()
        return projects
