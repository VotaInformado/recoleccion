# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import Authorship
from recoleccion.serializers.parties import PartyInfoSerializer
from recoleccion.serializers.persons import PersonModelSerializer
from recoleccion.serializers.law_projects import LawProjectListSerializer


class AuthorshipModelSerializer(serializers.ModelSerializer):
    party = PartyInfoSerializer()
    person = PersonModelSerializer()
    project = LawProjectListSerializer()

    class Meta:
        model = Authorship
        fields = "__all__"
        read_only_fields = ["id"]


class LawProjectAuthorsSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()

    class Meta:
        model = Authorship
        fields = ["person", "party", "author_type"]
        depth = 1

    def get_person(self, obj):
        from recoleccion.serializers.persons import PersonModelSerializer

        return PersonModelSerializer(obj.person).data

    def to_representation(self, instance):
        # we put all the info at the top level
        data = super().to_representation(instance)
        data = {**data, **data.pop("person")}
        data.pop("person")
        data["full_name"] = data["name"] + " " + data["last_name"]
        data["party"] = data["party"]["main_denomination"]
        return data


class NeuralNetworkAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authorship
        fields = ["party", "person", "project"]


class AuthorsProjectsCountSerializer(serializers.Serializer):
    """
    We use Method Fields because currently the serializer is receiving Person object
    with the authorship_count attribute added by the queryset. Thus, we separate them
    manually.
    """

    person = serializers.SerializerMethodField()
    authorship_count = serializers.SerializerMethodField()

    def get_person(self, obj):
        return PersonModelSerializer().to_representation(obj)

    def get_authorship_count(self, obj):
        return obj.authorship_count


class ReducedAuthorSerializer(serializers.ModelSerializer):
    # Used for prediction only, we just need the party
    class Meta:
        model = Authorship
        fields = ["party_id"]
