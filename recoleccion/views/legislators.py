# Django rest framework
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from recoleccion.components.services.news.news_provider import NewsProvider

# Project
from recoleccion.models.person import Person
from recoleccion.models.vote import Vote
from recoleccion.models.law_project import LawProject
from recoleccion.serializers.news import LegislatorNewsResponseSerializer
from recoleccion.serializers.votes import VoteModelSerializer
from recoleccion.serializers.law_projects import LawProjectListSerializer
from recoleccion.models.authorship import Authorship
from recoleccion.serializers.legislators import (
    LegislatorDetailsSerializer,
    LegislatorInfoSerializer,
    NeuralNetworkLegislatorSerializer,
)
from recoleccion.utils.documentation import LEGISLATORS_NEWS_DESCRIPTION


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
        responses={status.HTTP_200_OK: LegislatorNewsResponseSerializer},
        operation_description=LEGISLATORS_NEWS_DESCRIPTION,
    )
    @action(detail=True, methods=["get"], url_path="news")
    def get_legislator_news(self, request, pk=None):
        legislator: Person = self.get_object()
        legislator_news = NewsProvider.get_legislator_news(legislator)
        response = LegislatorNewsResponseSerializer(legislator_news).data
        return Response(response)


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
        law_projects_ids = Authorship.objects.filter(person_id=legislator_id).values_list("project_id", flat=True)
        return LawProject.objects.filter(id__in=law_projects_ids)
