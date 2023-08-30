# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models import Authorship


class AuthorshipModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authorship
        fields = "__all__"
        read_only_fields = ["id"]


class LawProjectAuthorsSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()

    class Meta:
        model = Authorship
        fields = ["person", "party", "author_type"]

    def get_person(self, obj):
        from recoleccion.serializers.persons import PersonModelSerializer

        return PersonModelSerializer(obj.person).data

    # def to_representation(self, instance): TODO: definir cómo se devuelve esto
    #     # we put all the info at the top level
    #     data = super().to_representation(instance)
    #     data = {**data, **data.pop("person")}
    #     data.pop("person")
    #     return data
