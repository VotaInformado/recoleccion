from django.db import models


class LinkingDecisions(models.TextChoices):
    APPROVED = "APPROVED", "Aprobado"
    DENIED = "DENIED", "Denegado"
