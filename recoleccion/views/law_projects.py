# Django rest framework
from rest_framework import viewsets, mixins
from recoleccion.serializers.law_projects import LawProjectListSerializer, LawProjectRetrieveSerializer

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