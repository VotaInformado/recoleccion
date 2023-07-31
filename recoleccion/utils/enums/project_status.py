from django.db import models
from rest_framework import serializers

class ProjectStatus(models.TextChoices):
    # Ongoing status
    ORIGIN_CHAMBER_COMISSION = "ORIGIN_CHAMBER_COMISSION", "En comisiones, cámara de origen"
    ORIGIN_CHAMBER_SENTENCE = "ORIGIN_CHAMBER_SENTENCE", "Con dictamen de comisiones, cámara de origen"
    HALF_SANCTION = "HALF_SANCTION", "Media sanción"
    REVISION_CHAMBER_COMISSION = "REVISION_CHAMBER_COMISSION", "En comisiones, cámara revisora"
    REVISION_CHAMBER_SENTENCE = "REVISION_CHAMBER_SENTENCE", "Con dictamen de comisiones, cámara revisora"
    # Finished status
    WITHDRAWN = "WITHDRAWN", "Retirado"
    APPROVED = "APPROVED", "Aprobado"
    REJECTED = "REJECTED", "Rechazado"

    def __str__(self):
        return self.value
    
class ProjectStatusSerializer(serializers.Field):
    def to_representation(self, obj):
        return ProjectStatus(obj).label

    def to_internal_value(self, data):
        return ProjectStatus(data).value