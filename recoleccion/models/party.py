# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class PartyRelationTypes(models.TextChoices):
    ALTERNATIVE_DENOMINATION = "ALTERNATIVE_DENOMINATION", "Denominación alternativa"
    SUB_PARTY = "SUB_PARTY", "Sub partido"


class Party(BaseModel):
    main_denomination = models.CharField(max_length=200, unique=True, null=False)


class PartyDenomination(BaseModel):
    class Meta:
        unique_together = ("party", "denomination")

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="denominations")
    denomination = models.CharField(max_length=200)
    relation_type = models.CharField(
        max_length=50,
        choices=PartyRelationTypes.choices,
        default=PartyRelationTypes.ALTERNATIVE_DENOMINATION,
    )
