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
    votes = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ["id"]

    def get_votes(self, obj):
        from django.db.models import Count, Q
        from recoleccion.utils.enums.vote_choices import VoteChoices
        votes = obj.votes.all()
        votes_summary = votes.aggregate(
            afirmatives=Count("vote", filter=Q(vote=VoteChoices.POSITIVE.label)),
            negatives=Count("vote", filter=Q(vote=VoteChoices.NEGATIVE.label)),
            abstentions=Count("vote", filter=Q(vote=VoteChoices.ABSTENTION.label)),
            absents=Count("vote", filter=Q(vote=VoteChoices.ABSENT.label)),
        )
        return votes_summary

    def get_legislator_seats(self, obj):
        senate_seats = ReducedSenateSeatSerializer(
            obj.senate_seats.all(), many=True
        ).data
        deputy_seats = ReducedDeputySeatSerializer(
            obj.deputy_seats.all(), many=True
        ).data
        all_seats = senate_seats + deputy_seats
        return sorted(all_seats, key=lambda seat: seat["start_of_term"], reverse=True)
