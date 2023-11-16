# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeatSerializer


class PersonModelSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()

    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ["id"]


class ReducedPersonSerializer(serializers.Serializer):
    person = serializers.SerializerMethodField()

    def get_person(self, obj: Person):
        return obj.id
