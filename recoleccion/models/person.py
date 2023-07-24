# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class PersonSex(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"


class Person(BaseModel):
    class Meta:
        app_label = "recoleccion"

    dni = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(7)], null=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True)
    sex = models.CharField(choices=PersonSex.choices, max_length=1, null=True)
    last_seat = models.CharField(choices=LegislatorSeats.choices, max_length=10, null=True)
    is_active = models.BooleanField(default=False)
