# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel


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

