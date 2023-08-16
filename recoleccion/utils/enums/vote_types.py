from django.db import models
from rest_framework import serializers


class VoteTypes(models.TextChoices):
    # Ongoing status
    PARTICULAR = "PARTICULAR", "Particular"
    GENERAL = "GENERAL", "General"
    OTHER = "OTHER", "Otro"
