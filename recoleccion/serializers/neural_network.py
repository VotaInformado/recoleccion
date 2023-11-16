from rest_framework import serializers

# Project
from recoleccion.models import LawProject, Person, Authorship


class ReducedLawProjectSerializer(serializers.Serializer):