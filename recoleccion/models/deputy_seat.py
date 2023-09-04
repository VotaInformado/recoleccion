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
    party_name = models.CharField(max_length=150)
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="deputy_seats", null=True)
    start_of_term = models.DateField()
    end_of_term = models.DateField()

    def __str__(self):
        return f"{self.person.name} {self.person.last_name}: {self.start_of_term} - {self.end_of_term}"
