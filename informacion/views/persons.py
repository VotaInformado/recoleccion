# Django rest framework
from rest_framework import viewsets, mixins

# Serializers
from informacion.serializers.persons import PersonModelSerializer

# Models
from library.models.person import Person


class PersonViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin):
    # TODO: sacar CreateModelMixin
    queryset = Person.objects.all()
    serializer_class = PersonModelSerializer
