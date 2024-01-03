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
    NeuralNetworkLegislatorSerializer,
)
from recoleccion.models.person import Person
from recoleccion.models.vote import Vote
from recoleccion.models.law_project import LawProject
from recoleccion.serializers.votes import VoteModelSerializer
from recoleccion.serializers.law_projects import LawProjectListSerializer
from django_filters.rest_framework import DjangoFilterBackend


class LegislatorsViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
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


class NeuralNetworkLegislatorViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkLegislatorSerializer
    queryset = Person.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }


class LegislatorLawProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = LawProjectListSerializer

    filterset_fields = {
        "origin_chamber": ["exact"],
        "status": ["in"],
        "publication_date": ["gte", "lte"],
    }
    ordering_fields = ["title", "publication_date", "status"]
    search_fields = ["title"]

    def get_queryset(self):
        legislator_id = self.kwargs.get("legislator_id")
        law_projects_ids = Authorship.objects.filter(
            person_id=legislator_id
        ).values_list("project_id", flat=True)
        return LawProject.objects.filter(id__in=law_projects_ids)
