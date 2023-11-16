# Django rest framework
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema

# Project
from recoleccion.models import SenateSeat
from recoleccion.serializers.prediction import PredictionRequestSerializer, PredictionResponseSerializer


class PredictionViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        methods=["post"],
        request_body=PredictionRequestSerializer,
        responses={status.HTTP_200_OK: PredictionResponseSerializer},
        operation_description="Retrieves active deputies only",
    )
    @action(detail=False, methods=["post"], url_path="active")
    def predict_vote(self, request):
        serializer = PredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prediction = predict_vote(serializer.data)
        response = PredictionResponseSerializer(prediction)
        return Response(serializer.data)

    