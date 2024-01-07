# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import Law


class LawModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Law
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1
