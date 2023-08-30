# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models import Authorship, LawProject, VoteSession
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
from recoleccion.serializers.vote_sessions import VoteSessionSerializer


class LawProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawProject
        fields = "__all__"
        read_only_fields = ["id"]


class LawProjectRetrieveSerializer(serializers.ModelSerializer):
    senate_vote_session = serializers.SerializerMethodField()
    deputies_vote_session = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()

    class Meta:
        model = LawProject
        fields = "__all__"
        read_only_fields = ["id"]

    def get_senate_vote_session(self, obj):
        senate_votes = obj.votes.filter(chamber=ProjectChambers.SENATORS)
        if not senate_votes:
            return None
        vote_session = VoteSession(senate_votes)
        return VoteSessionSerializer(vote_session).data

    def get_deputies_vote_session(self, obj):
        deputies_votes = obj.votes.filter(chamber=ProjectChambers.DEPUTIES)
        if not deputies_votes:
            return None
        vote_session = VoteSession(deputies_votes)
        return VoteSessionSerializer(vote_session).data

    def get_authors(self, obj: LawProject):
        from recoleccion.serializers.authors import LawProjectAuthorsSerializer

        if obj.origin_chamber == ProjectChambers.SENATORS:
            authors = Authorship.objects.filter(law_project=obj, author_type=LegislatorSeats.SENATOR)
        else:
            authors = Authorship.objects.filter(law_project=obj, author_type=LegislatorSeats.DEPUTY)
        return LawProjectAuthorsSerializer(authors, many=True).data


class LawProjectBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawProject
        fields = ["title", "publication_date", "status"]
