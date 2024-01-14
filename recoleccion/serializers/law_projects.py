# Django REST Framework
from rest_framework import serializers

# Project
from recoleccion.models import Authorship, LawProject, VoteSession
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.legislator_seats import LegislatorSeats
from recoleccion.serializers.vote_sessions import VoteSessionSerializer


class LawProjectListSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()

    class Meta:
        model = LawProject
        fields = "__all__"
        read_only_fields = ["id"]

    def get_year(self, obj: LawProject):
        return obj.get_year()


class LawProjectRetrieveSerializer(serializers.ModelSerializer):
    senate_vote_session = serializers.SerializerMethodField()
    deputies_vote_session = serializers.SerializerMethodField()
    votings = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    origin_chamber = serializers.SerializerMethodField()

    class Meta:
        model = LawProject
        fields = "__all__"
        read_only_fields = ["id"]

    def get_votings(self, obj):
        votings = []
        for value, label in ProjectChambers.choices:
            votes = obj.votes.filter(chamber=value)
            if not votes:
                continue
            vote_session = VoteSession(votes)
            serialized_session = VoteSessionSerializer(vote_session)
            votings.append(serialized_session.data)
        return votings

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

        if obj.get_origin_chamber() == ProjectChambers.SENATORS:
            authors = Authorship.objects.filter(project=obj, author_type=LegislatorSeats.SENATOR)
        else:
            authors = Authorship.objects.filter(project=obj, author_type=LegislatorSeats.DEPUTY)
        return LawProjectAuthorsSerializer(authors, many=True).data

    def get_origin_chamber(self, obj: LawProject):
        return obj.get_origin_chamber()


class LawProjectBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawProject
        fields = ["title", "publication_date", "status"]


class NeuralNetworkProjectSerializer(serializers.ModelSerializer):
    project_year = serializers.SerializerMethodField()
    project_text = serializers.SerializerMethodField()
    project_title = serializers.CharField(source="title", read_only=True)
    project_id = serializers.CharField(source="id", read_only=True)

    class Meta:
        model = LawProject
        fields = ["project_id", "project_text", "project_title", "project_year"]

    def get_project_year(self, obj: LawProject):
        return obj.publication_date.year

    def get_project_text(self, obj: LawProject):
        # If the project has no text, return a dot because the neural network
        # can't predict without text
        return obj.text or "."


class FittingDataValidationSerializer(serializers.Serializer):
    last_fetch_date = serializers.DateField()


class TextSummaryResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
