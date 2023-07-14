# Django rest framework
from rest_framework import viewsets, mixins

# Serializers
from recoleccion.serializers.persons import PersonModelSerializer

# Models
from vi_library.models.person import Person


class PersonViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Person.objects.all()
    serializer_class = PersonModelSerializer
