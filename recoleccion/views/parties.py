# Django rest framework
from rest_framework import viewsets, mixins
from django.db.models import Q, Count

# Serializers
from recoleccion.serializers.parties import PartyInfoSerializer, PartyDetailsSerializer
from recoleccion.serializers.authors import (
    AuthorshipModelSerializer,
    AuthorsProjectsCountSerializer,
)
from recoleccion.serializers.law_projects import LawProjectListSerializer

# Models
from recoleccion.models import Party, Authorship, LawProject, Person


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
