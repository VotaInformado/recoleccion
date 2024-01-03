from rest_framework import serializers


class PredictionRequestSerializer(serializers.Serializer):
    person_id = serializers.IntegerField(required=False)
    law_project_id = serializers.IntegerField()

class PredictionResponseSerializer(serializers.Serializer):
    legislator = serializers.IntegerField()
    vote = serializers.CharField()
