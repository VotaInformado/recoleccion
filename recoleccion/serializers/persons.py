# Django REST Framework
from rest_framework import serializers

# Models
from recoleccion.models.person import Person


class PersonModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "dni", "name", "last_name", "date_of_birth", "sex"]
        read_only_fields = ["id"]
