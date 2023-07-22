from django.db import models
from rest_framework import serializers
import json

class LegislatorSeats(models.TextChoices):
    SENATOR = "SENATOR", "Senador"
    DEPUTY = "DEPUTY", "Diputado"

    def __str__(self):
        return self.value
    
class LegislatorSeatSerializer(serializers.Field):
    def to_representation(self, obj):
        return LegislatorSeats(obj).label

    def to_internal_value(self, data):
        return LegislatorSeats(data).value