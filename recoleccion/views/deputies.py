# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

# Models
from vi_library.models import DeputySeat

from recoleccion.serializers.deputies import ActiveDeputiesSerializer, DeputySeatModelSerializer


class DeputiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = DeputySeat.objects.all()
    serializer_class = DeputySeatModelSerializer

    @action(detail=False, methods=["get"], url_path="active")
    def get_active_deputies(self, request):
        serializer = ActiveDeputiesSerializer(self.queryset, many=True)
        return Response(serializer.data)