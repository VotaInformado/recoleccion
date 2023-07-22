# Django REST Framework
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import (
    ReturnDict,
)

# Models
from recoleccion.models.person import Person

# Serializers
from recoleccion.utils.enums.legislator_seats import LegislatorSeatSerializer


class LegislatorInfoSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()
    class Meta:
        model = Person
        fields = '__all__'
