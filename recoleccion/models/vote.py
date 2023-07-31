# Django
from django.db import models

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_choices import VoteChoices

class Vote(BaseModel):
    chamber = models.CharField(choices=ProjectChambers.choices, max_length=10)
    person = models.ForeignKey("Person", on_delete=models.CASCADE, null=True)
    person_name = models.CharField(max_length=100, null=True)  # only in case of not finding the person
    person_last_name = models.CharField(max_length=100, null=True)  # only in case of not finding the person
    party = models.CharField(max_length=200, null=True)
    province = models.CharField(max_length=200, null=True)
    vote = models.CharField(choices=VoteChoices.choices, max_length=15)
    project = models.ForeignKey("LawProject", on_delete=models.CASCADE, null=True)
    law = models.ForeignKey("Law", on_delete=models.CASCADE, null=True)
    reference = models.CharField(max_length=200, null=True, help_text="Reference in case of not finding the project or law")
    reference_description = models.TextField(null=True)
    source = models.CharField(max_length=100, null=True)
