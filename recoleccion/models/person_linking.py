# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class PersonLinkingDecisions(models.TextChoices):
    APPROVED = "APPROVED", "Aprobado"
    DENIED = "DENIED", "Denegado"


class PersonLinking(BaseModel):
    full_name = models.CharField(max_length=200)
    compared_against = models.CharField(max_length=200, null=True)
    decision = models.CharField(choices=PersonLinkingDecisions.choices, max_length=10, null=True)
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="linking")

    def is_approved(self):
        return self.decision == PersonLinkingDecisions.APPROVED

    def is_denied(self):
        return self.decision == PersonLinkingDecisions.DENIED
