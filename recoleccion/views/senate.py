# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

# Models
from recoleccion.models import SenateSeat

from recoleccion.serializers.senate import SenateSeatModelSerializer


class SenateViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = SenateSeat.objects.all()
    active_queryset = SenateSeat.objects.filter(is_active=True)
    serializer_class = SenateSeatModelSerializer

    @action(detail=False, methods=["get"], url_path="active")
    def get_active_senators(self, request):
        serializer = SenateSeatModelSerializer(self.active_queryset, many=True)
        return Response(serializer.data)
