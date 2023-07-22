from django.db import models

class LegislatorSeats(models.TextChoices):
    SENATOR = "SENATOR", "Senador"
    DEPUTY = "DEPUTY", "Diputado"
