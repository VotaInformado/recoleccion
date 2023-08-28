from django.db import models
from rest_framework import serializers


class ProjectChambers(models.TextChoices):
    SENATORS = "SENATORS", "Cámara de Senadores"
    DEPUTIES = "DEPUTIES", "Cámara de Diputados"

    def __str__(self):
        return self.value


class ProjectChambersSerializer(serializers.Field):
    def to_representation(self, obj):
        return ProjectChambers(obj).label

    def to_internal_value(self, data):
        return ProjectChambers(data).value
