# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

# Models
from recoleccion.models import DeputySeat

from recoleccion.serializers.deputies import DeputySeatModelSerializer


class DeputiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = DeputySeat.objects.all()
    serializer_class = DeputySeatModelSerializer

    def get_queryset(self):
        queryset = DeputySeat.objects.all()
        if self.action == "get_active_deputies":
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=False, methods=["get"], url_path="active")
    def get_active_deputies(self, request):
        serializer = DeputySeatModelSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)
