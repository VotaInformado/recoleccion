from django.db import models

# Base model
from recoleccion.models.base import BaseModel
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class Authorship(BaseModel):
    class Meta:
        unique_together = ("law_project", "person")

    law_project = models.ForeignKey("LawProject", on_delete=models.CASCADE, related_name="authorships", null=True)
    reference = models.CharField(max_length=150, help_text="In case the law project is not found", null=True)
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="authorships", null=True)
    person_name = models.CharField(max_length=150)
    person_last_name = models.CharField(max_length=150)
    party = models.CharField(max_length=150)
    author_type = models.CharField(choices=LegislatorSeats.choices, max_length=10)
    source = models.CharField(max_length=150)
