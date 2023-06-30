"""Transaction views."""

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import View
from informacion.models.person import Person
from rest_framework import viewsets, mixins


class PersonViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Person.objects.all()
    
