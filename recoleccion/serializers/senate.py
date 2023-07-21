# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import SenateSeat


class ReducedSenateSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenateSeat
        exclude = ["person"]


class SenateSeatModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenateSeat
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1
