# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

# Models
from recoleccion.models import Authorship

from recoleccion.serializers.authors import NeuralNetworkAuthorSerializer


class NeuralNetworkAuthorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkAuthorSerializer
    queryset = Authorship.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }
