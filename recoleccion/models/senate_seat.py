from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class SenateSeat(BaseModel):
    class Meta:
        app_label = "recoleccion"
        unique_together = ("person_id", "start_of_term", "end_of_term")

    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="senate_seats")
    province = models.CharField(max_length=100)
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="senate_seats", null=True)
    party_name = models.CharField(max_length=150)
    start_of_term = models.DateField()
    end_of_term = models.DateField()

    def __str__(self):
        return f"{self.person.name} {self.person.last_name}: {self.start_of_term} - {self.end_of_term}"