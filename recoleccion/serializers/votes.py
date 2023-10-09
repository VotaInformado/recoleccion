# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models import Vote
from recoleccion.utils.enums.project_chambers import ProjectChambers


class VoteModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = "__all__"
        read_only_fields = ["id"]


class LegislatorVoteSerializer(serializers.ModelSerializer):
    from recoleccion.serializers.law_projects import LawProjectBasicInfoSerializer

    project = LawProjectBasicInfoSerializer()
    project_id = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = ["project_id", "project", "vote", "date", "chamber"]

    def get_project_id(self, obj: Vote):
        if not obj.project:
            return None
        if obj.chamber == ProjectChambers.SENATORS:
            return obj.project.senate_project_id
        else:
            return obj.project.deputies_project_id

    def to_representation(self, instance):
        data = super().to_representation(instance)
        project_id = data.pop("project_id")
        if project_id:
            data["project"]["project_id"] = project_id
        else:
            data["project"] = None
        return data


class BasicVoteInfoSerializer(serializers.ModelSerializer):
    from recoleccion.serializers.persons import PersonModelSerializer

    person = PersonModelSerializer()

    class Meta:
        model = Vote
        fields = ["person", "vote", "date", "chamber"]
