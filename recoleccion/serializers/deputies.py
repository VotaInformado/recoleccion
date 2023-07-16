# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import DeputySeat


class DeputySeatModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeputySeat
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1


class ActiveDeputiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeputySeat
        fields = "__all__"
        read_only_fields = ["id"]
        queryset = DeputySeat.objects.filter(is_active=True)
        depth = 1
