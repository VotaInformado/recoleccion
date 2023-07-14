# Django rest framework
from requests import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

# Serializers
from recoleccion.serializers.persons import PersonModelSerializer

# Models
from vi_library.models import SenateSeat

from recoleccion.serializers.senate import ActiveSenatorsSerializer, SenateSeatModelSerializer


class SenateViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = SenateSeat.objects.all()
    serializer_class = SenateSeatModelSerializer

    @action(detail=False, methods=["get"], url_path="active")
    def get_active_senators(self, request):
        serializer = ActiveSenatorsSerializer(self.queryset, many=True)
        return Response(serializer.data)