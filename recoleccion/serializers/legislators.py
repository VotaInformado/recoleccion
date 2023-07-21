# Django REST Framework
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import (
    ReturnDict,
)

# Models
from recoleccion.models.person import Person

# Serializers
from recoleccion.serializers.deputies import ReducedDeputySeatSerializer
from recoleccion.serializers.senate import ReducedSenateSeatSerializer


class LegislatorInfoSerializer(serializers.ModelSerializer):
    legislator_seats = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = '__all__'


    def get_legislator_seats(self, obj):
        senate_seats = ReducedSenateSeatSerializer(obj.senate_seats.all(), many=True).data
        deputy_seats = ReducedDeputySeatSerializer(obj.deputy_seats.all(), many=True).data
        return senate_seats + deputy_seats
