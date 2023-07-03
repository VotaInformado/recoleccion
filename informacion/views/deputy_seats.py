# Django rest framework
from rest_framework import viewsets, mixins

# Serializers
from informacion.serializers.deputy_seats import DeputySeatModelSerializer

# Models
from vi_library.models.deputy_seat import DeputySeat


class DeputySeatsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin):
    # TODO: sacar CreateModelMixin
    queryset = DeputySeat.objects.all()
    serializer_class = DeputySeatModelSerializer
