# Django rest framework
from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response


# Project
from recoleccion.components.services.news.news_provider import NewsProvider

from recoleccion.serializers.news import (
    GeneralNewsRequestSerializer,
    GeneralNewsResponseSerializer,
)
from recoleccion.utils.documentation import PREDICTION_ENDPOINT_DESCRIPTION


class NewsViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        methods=["get"],
        request_query_serializer=GeneralNewsRequestSerializer,
        responses={status.HTTP_200_OK: GeneralNewsResponseSerializer},
        operation_description=PREDICTION_ENDPOINT_DESCRIPTION,
    )
    @action(detail=False, methods=["get"], url_path="get-latest-news")
    def get_latest_news(self, request):
        request_serializer = GeneralNewsRequestSerializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        max_news = request_serializer.validated_data.get("max_news")
        news_service = NewsProvider()
        latest_news = news_service.get_global_news(max_news)
        response = GeneralNewsResponseSerializer(latest_news).data
        return Response(response)
