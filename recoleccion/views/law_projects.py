# Django rest framework
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema


# Project
from recoleccion.serializers.law_projects import (
    LawProjectListSerializer,
    LawProjectRetrieveSerializer,
    NeuralNetworkProjectSerializer,
    TextSummaryResponseSerializer,
)
from recoleccion.serializers.votes import VoteModelSerializer

from recoleccion.models import LawProject, Vote
from recoleccion.utils.documentation import TEXT_SUMMARIZATION_DESCRIPTION


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

    @swagger_auto_schema(
        methods=["get"],
        responses={status.HTTP_200_OK: TextSummaryResponseSerializer},
        operation_description=TEXT_SUMMARIZATION_DESCRIPTION,
    )
    @action(detail=True, methods=["get"], url_path="summary")
    def summarize_project_text(self, request, pk=None):
        law_project: LawProject = self.get_object()
        project_summary = law_project.get_summary()
        serializer = TextSummaryResponseSerializer({"summary": project_summary})
        return Response(serializer.data)


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
        law_project_id = self.kwargs.get("law_project_id")
        if law_project_id:
            law_project = LawProject.objects.get(id=law_project_id)
            return law_project.votes.all()
        return Vote.objects.none()  # for swagger only


class NeuralNetworkProjectsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkProjectSerializer
    queryset = LawProject.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }
