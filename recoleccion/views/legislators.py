# Django rest framework
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

# Project
from recoleccion.views.responses.legislators import law_project_author_responses
from recoleccion.models.authorship import Authorship
from recoleccion.serializers.legislators import (
    LegislatorDetailsSerializer,
    LegislatorInfoSerializer,
)
from recoleccion.models.person import Person
from recoleccion.models.vote import Vote
from recoleccion.serializers.votes import VoteModelSerializer
from django_filters.rest_framework import DjangoFilterBackend


class LegislatorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    def get_serializer_class(self):
        if self.action == "list":
            return LegislatorInfoSerializer
        elif self.action == "retrieve":
            return LegislatorDetailsSerializer

    serializer_class = LegislatorInfoSerializer
    queryset = Person.objects.order_by("id").all()
    search_fields = ["name", "last_name"]
    filterset_fields = ["is_active", "last_seat"]
    ordering_fields = ["name", "last_name", "last_seat", "is_active"]

    @swagger_auto_schema(
        methods=["get"],
        responses=law_project_author_responses,
        operation_description="Retrieves the law projects of a legislator",
    )
    @action(detail=True, methods=["get"], url_path="law-projects")
    def get_law_projects(self, request, pk=None):
        from recoleccion.serializers.law_projects import LawProjectBasicInfoSerializer

        person = self.get_object()
        authorships = Authorship.objects.filter(person=person)
        law_projects = [authorship.law_project for authorship in authorships if authorship.law_project]
        # TODO: ver esto, qué hacemos con las authorships con referencias en lugar de law_projects
        response = LawProjectBasicInfoSerializer(law_projects, many=True).data
        return Response(response, status=status.HTTP_200_OK)


class LegislatorVotesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = VoteModelSerializer

    filterset_fields = {
        "chamber": ["exact"],
        "date": ["exact"],
        "vote": ["exact", "in"],
        "party_name": ["icontains"],
        "project__title": ["icontains"],
    }
    ordering_fields = ["vote", "party_name", "project__title", "date"]
    search_fields = ["project__title", "vote"]

    def get_queryset(self):
        legislator_id = self.kwargs.get("legislator_id")
        if legislator_id is not None:
            return Vote.objects.filter(person_id=legislator_id)
        return Vote.objects.none()  # for swagger only