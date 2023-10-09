# Django rest framework
from rest_framework import viewsets, mixins

# Serializers
from recoleccion.serializers.parties import PartyInfoSerializer, PartyDetailsSerializer

# Models
from recoleccion.models import Party


class PartiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Party.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PartyInfoSerializer
        elif self.action == "retrieve":
            return PartyDetailsSerializer
