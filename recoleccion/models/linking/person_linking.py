# Django
from django.db import models

# Project
from recoleccion.models.linking.linking_decision import LinkingDecision


class PersonLinkingDecision(LinkingDecision):
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="linking", null=True)
    messy_name = models.CharField(max_length=255, null=True, help_text="Messy full name")
