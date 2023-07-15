# Django REST Framework
from rest_framework import serializers

# Models
from vi_library.models import SenateSeat


class SenateSeatModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = SenateSeat
        fields = "__all__"
        read_only_fields = ["id"]
        depth = 1
