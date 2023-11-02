# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers


class BaseVoteSessionSerializer(serializers.Serializer):
    date = serializers.DateField()
    afirmatives = serializers.IntegerField()
    negatives = serializers.IntegerField()
    abstentions = serializers.IntegerField()
    absents = serializers.IntegerField()


class PartyVoteSessionSerializer(BaseVoteSessionSerializer):
    title = serializers.CharField()
    total_votes = serializers.IntegerField()


class VoteSessionSerializer(BaseVoteSessionSerializer):
    chamber = serializers.ChoiceField(choices=ProjectChambers.choices)
