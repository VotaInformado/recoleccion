from rest_framework import serializers


class PredictionRequestSerializer(serializers.Serializer):
    person = serializers.IntegerField(required=False)
    law_project = serializers.IntegerField()

class PredictionResponseSerializer(serializers.Serializer):
    legislator = serializers.IntegerField()
    vote = serializers.CharField()
