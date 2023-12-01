# Django
from django.db import models

# Project
from recoleccion.models.linking.linking_decision import LinkingDecision


class PartyLinkingDecision(LinkingDecision):
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="linking", null=True)
    messy_denomination = models.CharField(max_length=255, null=True, help_text="Messy denomination")
