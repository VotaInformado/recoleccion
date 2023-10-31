# Django rest framework
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response

# Serializers
from recoleccion.views.paginator import StandardResultsSetPagination
from recoleccion.serializers.parties import PartyInfoSerializer, PartyDetailsSerializer, PartyVoteSessionSerializer, PartyVotesRequestSerializer
from recoleccion.models import PartyVoteSession


# Models
from recoleccion.models import Party


class PartiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
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

    def _get_party_votes_per_project(self, party: Party, max_results):
        party_projects = party.get_voted_projects(max_results=max_results)
        votes_per_project = [project.votes.all() for project in party_projects]
        vote_sessions = [
            PartyVoteSession(project, vote_list, party) for project, vote_list in zip(party_projects, votes_per_project)
        ]
        vote_session_data = PartyVoteSessionSerializer(vote_sessions, many=True).data
        return vote_session_data

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
        max_results = serializer.validated_data.get("max_results")
        party: Party = self.get_object()
        vote_session_data = self._get_party_votes_per_project(party, max_results)
        page = self.paginate_queryset(vote_session_data)
        if page is None:
            return Response(vote_session_data, status=status.HTTP_200_OK)

        paginator = StandardResultsSetPagination()
        paginated_data = paginator.paginate_queryset(vote_session_data, request)
        serializer = PartyVoteSessionSerializer(paginated_data, many=True)
        return self.get_paginated_response(serializer.data)
