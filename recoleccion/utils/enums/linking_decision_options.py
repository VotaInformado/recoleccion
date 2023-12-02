from django.db import models


class LinkingDecisionOptions(models.TextChoices):
    APPROVED = "APPROVED", "Aprobado"
    DENIED = "DENIED", "Denegado"
    PENDING = "PENDING", "Pendiente"
