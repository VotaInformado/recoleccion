# Django rest framework
from rest_framework import viewsets, mixins, generics
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from recoleccion.serializers.law_projects import (
    LawProjectListSerializer,
    LawProjectRetrieveSerializer,
)
from recoleccion.serializers.votes import VoteModelSerializer
from recoleccion.views.responses.law_projects import law_project_votings_responses

# Models
from recoleccion.models import LawProject
from recoleccion.utils.enums.project_chambers import ProjectChambers


class LawProjectsViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    def get_serializer_class(self):
        if self.action == "list":
            return LawProjectListSerializer
        elif self.action == "retrieve":
            return LawProjectRetrieveSerializer

    queryset = LawProject.objects.order_by("id").all()
    search_fields = ["title"]
    filterset_fields = {
        "origin_chamber": ["exact"],
        "status": ["in"],
        "publication_date": ["gte", "lte"],
    }
    ordering_fields = ["title", "publication_date", "status"]


class LawProyectVotesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = VoteModelSerializer

    filterset_fields = {
        "chamber": ["exact"],
        "date": ["exact"],
        "vote": ["exact", "in"],
    }
    ordering_fields = ["vote"]
    search_fields = ["person__name", "person__last_name", "vote"]

    def get_queryset(self):
        law_project_id = self.kwargs["law_project_id"]
        law_project = LawProject.objects.get(id=law_project_id)
        return law_project.votes.all()
