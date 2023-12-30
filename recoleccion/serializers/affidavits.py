from rest_framework import serializers

# Project
from recoleccion.models.affidavit_entry import AffidavitEntry


class AffidavitBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffidavitEntry
        fields = ["year", "value"]
        read_only_fields = ["id"]
