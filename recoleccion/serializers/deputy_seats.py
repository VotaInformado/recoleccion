# Django REST Framework
from rest_framework import serializers

# Models
from vi_library.models.deputy_seat import DeputySeat


class DeputySeatModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeputySeat
        fields = ["id", "dni", "name", "last_name", "date_of_birth", "sex"]
        read_only_fields = ["id"]
