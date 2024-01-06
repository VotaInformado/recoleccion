# Django rest framework
from rest_framework import viewsets, mixins

# Serializers
from recoleccion.serializers.laws import LawModelSerializer

# Models
from recoleccion.models import Law


class LawsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Law.objects.order_by("id").all()
    serializer_class = LawModelSerializer

    search_fields = ["title", "law_number"]
    filterset_fields = {
        "publication_date": ["gte", "lte"],
    }
