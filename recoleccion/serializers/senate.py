# Django REST Framework
from rest_framework import serializers

# Models
from vi_library.models import SenateSeat

# Person serializer
from recoleccion.serializers.persons import PersonModelSerializer


class SenateSeatModelSerializer(serializers.ModelSerializer):
    # person = PersonModelSerializer()

    class Meta:
        model = SenateSeat
        fields = "__all__"
        read_only_fields = ["id"]


class ActiveSenatorsSerializer(serializers.ModelSerializer):
    # person = PersonModelSerializer()

    class Meta:
        model = SenateSeat
        fields = "__all__"
        read_only_fields = ["id"]
        queryset = SenateSeat.objects.filter(is_active=True)
