# Django rest framework
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

# Models
from recoleccion.models import SenateSeat

from recoleccion.serializers.senate import SenateSeatModelSerializer


class SenateViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = SenateSeatModelSerializer

    def get_queryset(self):
        queryset = SenateSeat.objects.all()
        if self.action == "get_active_senators":
            queryset = queryset.filter(person__is_active=True)
        return queryset

    @swagger_auto_schema(
        responses={200: SenateSeatModelSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="active")
    def get_active_senators(self, request):
        serializer = SenateSeatModelSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)
