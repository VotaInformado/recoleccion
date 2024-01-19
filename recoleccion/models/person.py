# Django
from django.db import models
from django.core.validators import MinLengthValidator

# Base model
from recoleccion.models.base import BaseModel
from recoleccion.models.law_project import LawProject

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

    def __str__(self):
        base_str = f"{self.name} {self.last_name}, last seat: {self.last_seat}"
        if self.is_active:
            return f"{base_str} (active)"
        return base_str

    @property
    def law_projects(self):
        return LawProject.objects.filter(authorships__person=self)

    @property
    def full_name(self):
        return f"{self.name} {self.last_name}"

    @property
    def formal_full_name(self):
        return f"{self.last_name} {self.name}"

    @property
    def last_party(self):
        if self.last_seat == "Diputados":
            last_deputy_seat = self.deputy_seats.order_by("-end_of_term").first()
            last_party = last_deputy_seat.party
        elif self.last_seat == "Senado":
            last_senate_seat = self.senate_seats.order_by("-end_of_term").first()
            last_party = last_senate_seat.party
        last_deputy_seat = self.deputy_seats.order_by("-end_of_term").first()
        last_senate_seat = self.senate_seats.order_by("-end_of_term").first()
        if not last_deputy_seat:
            return last_senate_seat.party if last_senate_seat else None
        if not last_senate_seat:
            return last_deputy_seat.party
        if last_deputy_seat.end_of_term > last_senate_seat.end_of_term:
            last_party = last_deputy_seat.party
        else:
            last_party = last_senate_seat.party if last_senate_seat else None
        return last_party
