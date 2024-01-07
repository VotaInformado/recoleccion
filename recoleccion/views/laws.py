# Django rest framework
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, mixins, status
from recoleccion.serializers.law_projects import TextSummaryResponseSerializer

# Serializers
from recoleccion.serializers.laws import LawModelSerializer

# Models
from recoleccion.models import Law
from recoleccion.utils.documentation import TEXT_SUMMARIZATION_DESCRIPTION


class LawsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Law.objects.order_by("id").all()
    serializer_class = LawModelSerializer

    search_fields = ["title", "law_number"]
    filterset_fields = {
        "publication_date": ["gte", "lte"],
    }

    @swagger_auto_schema(
        methods=["get"],
        responses={status.HTTP_200_OK: TextSummaryResponseSerializer},
        operation_description=TEXT_SUMMARIZATION_DESCRIPTION,
    )
    @action(detail=True, methods=["get"], url_path="summary")
    def summarize_project_text(self, request, pk=None):
        law: Law = self.get_object()
        project_summary = law.get_ai_summary()
        serializer = TextSummaryResponseSerializer({"summary": project_summary})
        return Response(serializer.data)
