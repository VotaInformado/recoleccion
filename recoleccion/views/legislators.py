# Django rest framework
from rest_framework import viewsets, mixins
from recoleccion.serializers.legislators import LegislatorInfoSerializer

# Serializers
from recoleccion.serializers.persons import PersonModelSerializer

# Models
from recoleccion.models.person import Person


class LegislatorsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    
    serializer_class = LegislatorInfoSerializer
    queryset = Person.objects.all()
