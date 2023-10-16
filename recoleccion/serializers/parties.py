# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models import Party
from recoleccion.serializers.persons import PersonModelSerializer
from recoleccion.serializers.law_projects import LawProjectBasicInfoSerializer
from recoleccion.serializers.votes import BasicVoteInfoSerializer


class PartyInfoSerializer(serializers.ModelSerializer):
    alternative_denominations = serializers.SerializerMethodField()
    sub_parties = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = "__all__"

    def get_alternative_denominations(self, obj: Party):
        return obj.alternative_denominations

    def get_sub_parties(self, obj: Party):
        return obj.sub_parties


class PartyDetailsSerializer(serializers.ModelSerializer):
    alternative_denominations = serializers.SerializerMethodField()
    sub_parties = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    law_projects = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = "__all__"

    def get_alternative_denominations(self, obj: Party):
        return obj.alternative_denominations

    def get_sub_parties(self, obj: Party):
        return obj.sub_parties

    def get_members(self, obj: Party):
        members = obj.members
        members_data = PersonModelSerializer(members, many=True).data
        return members_data

    def get_law_projects(self, obj: Party):
        law_projects = obj.law_projects
        projects_data = LawProjectBasicInfoSerializer(law_projects, many=True).data
        return projects_data

    def get_votes(self, obj: Party):
        votes = obj.votes
        vote_sessions = BasicVoteInfoSerializer(votes, many=True).data
        return vote_sessions
