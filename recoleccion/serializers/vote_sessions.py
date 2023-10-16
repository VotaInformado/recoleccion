# Django REST Framework
from rest_framework import serializers
# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers


class VoteSessionSerializer(serializers.Serializer):
    chamber = serializers.ChoiceField(choices=ProjectChambers.choices)
    date = serializers.DateField()
    # votes_summary = serializers.DictField()
    afirmatives = serializers.IntegerField()
    negatives = serializers.IntegerField()
    abstentions = serializers.IntegerField()
    absents = serializers.IntegerField()

