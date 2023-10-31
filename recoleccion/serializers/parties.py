# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models import Party, PartyVoteSession
from recoleccion.serializers.persons import PersonModelSerializer
from recoleccion.serializers.law_projects import LawProjectBasicInfoSerializer
from recoleccion.serializers.vote_sessions import PartyVoteSessionSerializer
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
        from django.db.models import Q
        from recoleccion.models import Person, DeputySeat, SenateSeat, Vote, Authorship

        # members_query = (
        #     Q(deputy_seats__party=obj)
        #     | Q(senate_seats__party=obj)
        #     | Q(votes__party=obj)
        #     | Q(authorships__party=obj)
        # )
        # count = Person.objects.filter(members_query).distinct().count()

        deputy_seats = DeputySeat.objects.filter(party=obj).values("person_id").distinct()
        senate_seats = SenateSeat.objects.filter(party=obj).values("person_id").distinct()
        votes = Vote.objects.filter(party=obj).values("person_id").distinct()
        authorships = Authorship.objects.filter(party=obj).values("person_id").distinct()
        count = deputy_seats.union(senate_seats, votes, authorships).count()
        return count

    def get_country_representation(self, obj: Party):
        # Returns how many senate seats and deputy seats correspond to the party
        # grouped by province

        from recoleccion.models import DeputySeat, SenateSeat
        from recoleccion.utils.enums.provinces import Provinces

        # TODO: maybe filter seats by distinct people
        # members = Person.objects.filter(members_query).distinct()

        senate_seats = SenateSeat.objects.filter(party=obj).values_list("province")
        deputy_seats = DeputySeat.objects.filter(party=obj).values_list("district")
        # TODO make sure all provinces are equal
        representation = {province: 0 for province in Provinces.values}
        for province in representation.keys():
            representation[province] = {
                "senate_seats": senate_seats.filter(province=province).count(),
                "deputy_seats": deputy_seats.filter(district=province).count(),
                "province_name": Provinces(province).label,
            }

        return representation


class PartyVotesRequestSerializer(serializers.Serializer):
    max_results = serializers.IntegerField(
        required=False, allow_null=True, help_text="Limits the number of projects returned"
    )
