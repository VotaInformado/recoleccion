# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import DeputySeat, SenateSeat


class ReducedSenateSeatSerializer(serializers.ModelSerializer):
    chamber = serializers.ReadOnlyField(default="Senado")
    party_name = serializers.SerializerMethodField()

    class Meta:
        model = SenateSeat
        exclude = ["person"]

    def get_party_name(self, obj: DeputySeat | SenateSeat):
        return obj.party.main_denomination if obj.party else obj.party_name


class SenateSeatModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenateSeat
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1
