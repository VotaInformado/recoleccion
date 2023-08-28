# Django rest framework
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins

# Project
from recoleccion.views.responses.legislators import law_project_author_responses
from recoleccion.models.authorship import Authorship
from recoleccion.serializers.legislators import LegislatorDetailsSerializer, LegislatorInfoSerializer
from recoleccion.models.person import Person


class LegislatorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    def get_serializer_class(self):
        if self.action == "list":
            return LegislatorInfoSerializer
        elif self.action == "retrieve":
            return LegislatorDetailsSerializer

    serializer_class = LegislatorInfoSerializer
    queryset = Person.objects.all()

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
