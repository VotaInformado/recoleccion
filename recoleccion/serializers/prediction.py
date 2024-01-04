from rest_framework import serializers

from recoleccion.utils.enums.project_chambers import ProjectChambers


class PredictionRequestSerializer(serializers.Serializer):
    person_id = serializers.IntegerField()
    law_project_id = serializers.IntegerField()


class PredictionResponseSerializer(serializers.Serializer):
    legislator = serializers.IntegerField()
    vote = serializers.CharField()


class ChamberPredictionRequestSerializer(serializers.Serializer):
    chamber = serializers.ChoiceField(choices=ProjectChambers.choices)
    law_project_id = serializers.IntegerField()


class ChamberPredictionResponseSerializer(serializers.ListSerializer):
    child = PredictionResponseSerializer()
