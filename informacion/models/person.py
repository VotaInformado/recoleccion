# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from informacion.models.base import BaseModel

class PersonSex(models.TextChoices):
    MASCULINO = 'M', 'Masculino'
    FEMENINO = 'F', 'Femenino'


class Person(BaseModel):
    __tablename__ = "person"
    dni = models.CharField(max_length=8, unique=True, validators=[MinLengthValidator(7)])
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(choices=PersonSex.choices, max_length=1)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
