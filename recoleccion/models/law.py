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
    initial_file = models.CharField(max_length=30, null=True)
    associated_project = models.ForeignKey(
        "LawProject",
        on_delete=models.DO_NOTHING,
        related_name="associated_law",
        null=True,
        help_text="Proyecto de ley asociado",
    )
    project_id = models.CharField(max_length=30, null=True)  # in case the project is not found
    text = models.TextField(null=True)
    link = models.CharField(max_length=250, null=True)
