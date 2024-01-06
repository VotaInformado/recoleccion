# Django rest framework
from rest_framework import viewsets, mixins

# Models
from recoleccion.models import Authorship

from recoleccion.serializers.authors import AuthorshipModelSerializer, NeuralNetworkAuthorSerializer


class AuthorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = AuthorshipModelSerializer
    queryset = Authorship.objects.order_by("id").all()

    filterset_fields = {
        "chamber": ["exact"],
        "date": ["exact"],
        "vote": ["exact", "in"],
        "party_name": ["icontains"],
        "project__title": ["icontains"],
    }
    ordering_fields = ["vote", "party_name", "project__title", "date"]
    search_fields = ["project__title", "vote"]


class NeuralNetworkAuthorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkAuthorSerializer
    queryset = Authorship.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }
