# Django
from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class SocialData(BaseModel):
    class Meta:
        app_label = "recoleccion"

    # person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="social_data", null=True)
    person = models.OneToOneField("Person", on_delete=models.CASCADE, related_name="social_data", null=True)
    twitter = models.CharField(max_length=200, null=True)
    facebook = models.CharField(max_length=200, null=True)
    instagram = models.CharField(max_length=200, null=True)
    linkedin = models.CharField(max_length=200, null=True)
    tiktok = models.CharField(max_length=200, null=True)
    youtube = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=150, null=True)
    phone = models.CharField(max_length=50, null=True)
    picture_url = models.CharField(max_length=500, null=True)
    person_name = models.CharField(max_length=200, null=True)
    person_last_name = models.CharField(max_length=200, null=True)
