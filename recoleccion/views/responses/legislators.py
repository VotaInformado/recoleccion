from rest_framework import serializers, status
from drf_yasg import openapi

# Project
from recoleccion.serializers.authors import AuthorshipModelSerializer


law_project_authors_ok_response = openapi.Response("Law project authors", AuthorshipModelSerializer)

law_project_author_responses = {
    status.HTTP_200_OK: law_project_authors_ok_response,
    status.HTTP_400_BAD_REQUEST: openapi.Response("Bad request", None),
}
