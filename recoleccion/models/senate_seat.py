from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class SenateSeat(BaseModel):
    class Meta:
        app_label = "recoleccion"
        unique_together = ("person_id", "start_of_term", "end_of_term")

    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="senate_seat")
    province = models.CharField(max_length=100)
    party = models.CharField(max_length=150)
    start_of_term = models.DateField()
    end_of_term = models.DateField()
    is_active = models.BooleanField(default=False)
