# Django rest framework
from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

# Models
from recoleccion.models import DeputySeat

from recoleccion.serializers.deputies import DeputySeatModelSerializer


class DeputiesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = DeputySeat.objects.all()
    serializer_class = DeputySeatModelSerializer

    def get_queryset(self):
        queryset = DeputySeat.objects.all()
        if self.action == "get_active_deputies":
            queryset = queryset.filter(person__is_active=True)
        return queryset

    @swagger_auto_schema(
        methods=["get"],
        responses={status.HTTP_200_OK: DeputySeatModelSerializer},
        operation_description="Retrieves active deputies only",
    )
    @action(detail=False, methods=["get"], url_path="active")
    def get_active_deputies(self, request):
        serializer = DeputySeatModelSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)
