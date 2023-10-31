# Django rest framework
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from recoleccion.serializers.law_projects import (
    LawProjectListSerializer,
    LawProjectRetrieveSerializer,
    NeuralNetworkProjectSerializer,
)
from recoleccion.serializers.votes import VoteModelSerializer

# Models
from recoleccion.models import LawProject
from recoleccion.utils.enums.project_chambers import ProjectChambers


class LawProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
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


class LawProjectVotesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = VoteModelSerializer

    filterset_fields = {
        "chamber": ["exact"],
        "date": ["exact"],
        "vote": ["exact", "in"],
        "party_name": ["icontains"],
    }
    ordering_fields = ["vote", "person__name", "person__last_name", "party_name"]
    search_fields = ["person__name", "person__last_name", "vote"]

    def get_queryset(self):
        law_project_id = self.kwargs["law_project_id"]
        law_project = LawProject.objects.get(id=law_project_id)
        return law_project.votes.all()


class NeuralNetworkProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkProjectSerializer
    queryset = LawProject.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }
