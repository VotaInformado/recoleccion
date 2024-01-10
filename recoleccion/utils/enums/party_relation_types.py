from django.db import models


class PartyRelationTypes(models.TextChoices):
    ALTERNATIVE_DENOMINATION = "ALTERNATIVE_DENOMINATION", "Denominación alternativa"
    SUB_PARTY = "SUB_PARTY", "Sub partido"
