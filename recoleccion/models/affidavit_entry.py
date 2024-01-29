from django.db import models

# Project
from recoleccion.models.base import BaseModel
from recoleccion.utils.enums.affidavit import AffidevitType


class AffidavitEntry(BaseModel):
    # Affidavit = Declaración Jurada
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="affidavits", null=True)
    person_full_name = models.CharField(max_length=255)
    year = models.IntegerField()
    affidavit_type = models.CharField(choices=AffidevitType.choices, max_length=10)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    # details = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("person_full_name", "year")
