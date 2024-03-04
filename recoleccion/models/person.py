# Django
from django.db import models
from django.core.validators import MinLengthValidator
from django.core.exceptions import ObjectDoesNotExist

# Base model
from recoleccion.models.base import BaseModel
from recoleccion.models.deputy_seat import DeputySeat
from recoleccion.models.law_project import LawProject
from recoleccion.models.senate_seat import SenateSeat

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
    last_party = models.ForeignKey("Party", on_delete=models.SET_NULL, null=True)
    last_seat = models.CharField(choices=LegislatorSeats.choices, max_length=10, null=True)
    is_active = models.BooleanField(default=False)
    news_search_terms = models.CharField(max_length=200, null=True, help_text="Search terms for news API")
    name_corrected = models.BooleanField(default=False)

    def get_last_seat(self) -> DeputySeat | SenateSeat | None:
        deputy_seats = DeputySeat.objects.filter(person=self).order_by("-end_of_term")
        senate_seats = DeputySeat.objects.filter(person=self).order_by("-end_of_term")
        all_seats = list(deputy_seats) + list(senate_seats)
        all_seats.sort(key=lambda x: x.end_of_term, reverse=True)
        if not all_seats:
            return None
        return all_seats[0]

    def update_last_party_and_seat(self):
        last_seat: DeputySeat | SenateSeat = self.get_last_seat()
        if not last_seat:
            return False
        self.last_seat = last_seat.seat_type
        self.last_party = last_seat.party
        self.save()
        return True

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
    def picture_url(self):
        try:
            return self.social_data.picture_url
        except ObjectDoesNotExist:
            return None
