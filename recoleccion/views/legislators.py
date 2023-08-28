# Django rest framework
from rest_framework import viewsets, mixins
from recoleccion.serializers.legislators import (
    LegislatorDetailsSerializer,
    LegislatorInfoSerializer,
)

# Models
from recoleccion.models.person import Person


class LegislatorsViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    def get_serializer_class(self):
        if self.action == "list":
            return LegislatorInfoSerializer
        elif self.action == "retrieve":
            return LegislatorDetailsSerializer

    serializer_class = LegislatorInfoSerializer
    queryset = Person.objects.order_by("id").all()
