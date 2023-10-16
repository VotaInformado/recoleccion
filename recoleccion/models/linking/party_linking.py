# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


class PartyLinking(BaseModel):
    denomination = models.CharField(max_length=200)
    compared_against = models.CharField(max_length=200, null=True)
    decision = models.CharField(choices=LinkingDecisions.choices, max_length=10, null=True)
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="linking", null=True)

    def is_approved(self):
        return self.decision == LinkingDecisions.APPROVED

    def is_denied(self):
        return self.decision == LinkingDecisions.DENIED
