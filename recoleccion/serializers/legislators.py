# Django REST Framework
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import (
    ReturnDict,
)

# Project
from recoleccion.models.person import Person
from recoleccion.serializers.deputies import ReducedDeputySeatSerializer
from recoleccion.serializers.senate import ReducedSenateSeatSerializer
from recoleccion.serializers.votes import LegislatorVoteSerializer
from recoleccion.utils.enums.legislator_seats import LegislatorSeatSerializer


class LegislatorInfoSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()

    class Meta:
        model = Person
        fields = "__all__"


class LegislatorDetailsSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()
    legislator_seats = serializers.SerializerMethodField()
    votes = LegislatorVoteSerializer(many=True)  # TODO: solamente tiene que ir el resumen, el detalle va en legislators/x/votes

    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ["id"]

    def get_legislator_seats(self, obj):
        senate_seats = ReducedSenateSeatSerializer(obj.senate_seats.all(), many=True).data
        deputy_seats = ReducedDeputySeatSerializer(obj.deputy_seats.all(), many=True).data
        all_seats = senate_seats + deputy_seats
        return sorted(all_seats, key=lambda seat: seat["start_of_term"], reverse=True)
