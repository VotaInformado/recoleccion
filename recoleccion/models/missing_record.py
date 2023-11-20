import re
from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class MissingRecord(BaseModel):
    class_name = models.CharField(max_length=200)
    record_value = models.IntegerField(help_text="Year/page/period that is missing")
