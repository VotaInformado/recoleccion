# Django REST Framework
from rest_framework import serializers
# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.serializers.votes import VoteModelSerializer


class VoteSessionSerializer(serializers.Serializer):
    chamber = serializers.ChoiceField(choices=ProjectChambers.choices)
    date = serializers.DateField()
    votes_summary = serializers.DictField()
    votes = serializers.ListField(child=VoteModelSerializer())
