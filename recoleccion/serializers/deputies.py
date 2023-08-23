# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import DeputySeat


class ReducedDeputySeatSerializer(serializers.ModelSerializer):
    chamber = serializers.ReadOnlyField(default="Diputados")

    class Meta:
        model = DeputySeat
        exclude = ["person"]


class DeputySeatModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeputySeat
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1
