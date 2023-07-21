from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class DeputySeat(BaseModel):
    class Meta:
        app_label = "recoleccion"
        unique_together = ("person_id", "start_of_term", "end_of_term")

    deputy_id = models.CharField(max_length=10, null=True)
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="deputy_seats")
    district = models.CharField(max_length=150)
    party = models.CharField(max_length=150)
    start_of_term = models.DateField()
    end_of_term = models.DateField()
    is_active = models.BooleanField(default=False)
