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
    # members = serializers.SerializerMethodField()
    # law_projects = serializers.SerializerMethodField()
    # votes = serializers.SerializerMethodField()
    total_members = serializers.SerializerMethodField()
    country_representation = serializers.SerializerMethodField()

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

    def get_total_members(self, obj: Party):
        deputy_seats = obj.deputy_seats.values("person_id").distinct()
        senate_seats = obj.senate_seats.values("person_id").distinct()
        votes = obj.votes.values("person_id").distinct()
        authorships = obj.authorships.values("person_id").distinct()
        count = deputy_seats.union(senate_seats, votes, authorships).count()
        return count

    def get_country_representation(self, obj: Party):
        # Returns how many senate seats and deputy seats correspond to the party
        # grouped by province
        from recoleccion.utils.enums.provinces import Provinces

        representation = {province: 0 for province in Provinces.values}
        for province in representation.keys():
            senate_in_province = obj.deputy_seats.filter(district=province)
            deputy_in_province = obj.senate_seats.filter(province=province)
            votes = obj.votes.filter(province=province).values("person_id").distinct()
            senators = senate_in_province.values("person_id").distinct()
            deputies = deputy_in_province.values("person_id").distinct()

            representation[province] = {
                "senate_seats": senate_in_province.count(),
                "deputy_seats": deputy_in_province.count(),
                "total_members": senators.union(deputies, votes).count(),
                "province_name": Provinces(province).label,
            }

        return representation
