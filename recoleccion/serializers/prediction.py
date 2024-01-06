from rest_framework import serializers

# Project
from recoleccion.models import Person
from recoleccion.utils.enums.project_chambers import ProjectChambers


class PredictionRequestSerializer(serializers.Serializer):
    person_id = serializers.IntegerField()
    law_project_id = serializers.IntegerField()


class PredictionResponseSerializer(serializers.Serializer):
    legislator = serializers.IntegerField()
    vote = serializers.CharField()

    def to_representation(self, instance):
        legislator = Person.objects.get(id=instance["legislator"])
        legislator_info = {
            "id": legislator.id,
            "name": legislator.name,
            "last_name": legislator.last_name,
            "last_seat": legislator.last_seat,
        }
        return {"legislator": legislator_info, "vote": instance["vote"]}


class ChamberPredictionRequestSerializer(serializers.Serializer):
    chamber = serializers.ChoiceField(choices=ProjectChambers.choices, required=False)
    law_project_id = serializers.IntegerField()


class ChamberPredictionResponseSerializer(serializers.ListSerializer):
    child = PredictionResponseSerializer()
