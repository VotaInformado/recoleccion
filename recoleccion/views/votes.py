# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

# Models
from recoleccion.models.vote import Vote

from recoleccion.serializers.votes import NeuralNetworkVoteSerializer


class NeuralNetworkVotesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = NeuralNetworkVoteSerializer
    queryset = Vote.objects.all().order_by("-id")
    filterset_fields = {
        "created_at": ["gte", "lte"],
    }
