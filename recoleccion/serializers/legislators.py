# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models.person import Person
from recoleccion.serializers.affidavits import AffidavitBasicSerializer
from recoleccion.serializers.deputies import ReducedDeputySeatSerializer
from recoleccion.serializers.senate import ReducedSenateSeatSerializer
from recoleccion.serializers.law_projects import LawProjectBasicInfoSerializer
from recoleccion.utils.enums.legislator_seats import LegislatorSeatSerializer


class LegislatorInfoSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()
    last_party = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = "__all__"

    def get_last_party(self, obj: Person):
        return obj.last_party.main_denomination


class LegislatorDetailsSerializer(serializers.ModelSerializer):
    last_seat = LegislatorSeatSerializer()
    legislator_seats = serializers.SerializerMethodField()
    votes = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    affidavits = serializers.SerializerMethodField()
    last_party = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ["id"]

    def get_votes(self, obj):
        from django.db.models import Count, Q
        from recoleccion.utils.enums.vote_choices import VoteChoices

        votes = obj.votes.all()
        votes_summary = votes.aggregate(
            afirmatives=Count("vote", filter=Q(vote=VoteChoices.POSITIVE.value)),
            negatives=Count("vote", filter=Q(vote=VoteChoices.NEGATIVE.value)),
            abstentions=Count("vote", filter=Q(vote=VoteChoices.ABSTENTION.value)),
            absents=Count("vote", filter=Q(vote=VoteChoices.ABSENT.value)),
        )
        return votes_summary

    def get_projects(self, obj):
        from recoleccion.models import LawProject, Authorship

        law_projects_ids = Authorship.objects.filter(person_id=obj.id).values_list("project_id", flat=True)
        law_projects = LawProject.objects.filter(id__in=law_projects_ids)
        return LawProjectBasicInfoSerializer(law_projects, many=True).data

    def get_legislator_seats(self, obj):
        senate_seats = ReducedSenateSeatSerializer(obj.senate_seats.all(), many=True).data
        deputy_seats = ReducedDeputySeatSerializer(obj.deputy_seats.all(), many=True).data
        all_seats = senate_seats + deputy_seats
        return sorted(all_seats, key=lambda seat: seat["start_of_term"], reverse=True)

    def get_last_party(self, obj: Person):
        return obj.last_party.main_denomination if obj.last_party else None

    def get_affidavits(self, obj: Person):
        sorted_affidavits = obj.affidavits.order_by("year")
        return AffidavitBasicSerializer(sorted_affidavits, many=True).data


class NeuralNetworkLegislatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "last_name"]
