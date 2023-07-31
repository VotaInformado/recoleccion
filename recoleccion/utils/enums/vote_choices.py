from django.db import models
from rest_framework import serializers

class VoteChoices(models.TextChoices):
    # Ongoing status
    ABSENT = "ABSENT", "Ausente"
    ABSTENTION = "ABSTENTION", "Abstención"
    NEGATIVE = "NEGATIVE", "Negativo"
    POSITIVE = "POSITIVE", "Afirmativo"
    PRESIDENT = "PRESIDENT", "Presidente"  # no sé por qué pero aparentemente es una opción