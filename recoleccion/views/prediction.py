# Django rest framework
from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response


# Project
from recoleccion.components.services.neural_network import NeuralNetworkService
from recoleccion.models import Person, LawProject

from recoleccion.serializers.prediction import (
    ChamberPredictionRequestSerializer,
    ChamberPredictionResponseSerializer,
    PredictionRequestSerializer,
    PredictionResponseSerializer,
)
from recoleccion.utils.documentation import PREDICTION_ENDPOINT_DESCRIPTION


class PredictionViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        methods=["post"],
        request_body=PredictionRequestSerializer,
        responses={status.HTTP_200_OK: PredictionResponseSerializer},
        operation_description=PREDICTION_ENDPOINT_DESCRIPTION,
    )
    @action(detail=False, methods=["post"], url_path="predict-legislator-vote")
    def predict_legislator_vote(self, request):
        network_service = NeuralNetworkService()
        serializer = PredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prediction = network_service.get_legislator_prediction(serializer.validated_data)
        response = PredictionResponseSerializer(prediction).data
        return Response(response)

    @swagger_auto_schema(
        methods=["post"],
        request_body=ChamberPredictionRequestSerializer,
        responses={status.HTTP_200_OK: ChamberPredictionResponseSerializer},
        operation_description=PREDICTION_ENDPOINT_DESCRIPTION,
    )
    @action(detail=False, methods=["post"], url_path="predict-chamber-vote")
    def predict_chamber_vote(self, request):
        network_service = NeuralNetworkService()
        serializer = ChamberPredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prediction = network_service.get_chamber_prediction(serializer.validated_data)
        response = ChamberPredictionResponseSerializer(prediction).data
        return Response(response)
