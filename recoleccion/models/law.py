from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class Law(BaseModel):
    law_number = models.IntegerField(unique=True)
    title = models.TextField()
    summary = models.TextField()
    tags = models.TextField(null=True)
    publication_date = models.DateField(null=True)
    associated_decree = models.CharField(max_length=15, null=True)
    vetoed = models.BooleanField(default=False)
    initial_file = models.FileField(upload_to="laws", null=True, help_text="Expediente inicial")