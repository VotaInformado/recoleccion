from django.db import models

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.project_status import ProjectStatus


class LawProject(BaseModel):
    deputies_project_id = models.CharField(max_length=30, unique=True, null=True)
    senate_project_id = models.CharField(max_length=30, unique=True, null=True)
    origin_chamber = models.CharField(choices=ProjectChambers.choices, max_length=10)
    title = models.TextField()
    # no tiene resumen en principio
    publication_date = models.DateField(null=True)
    deputies_file = models.CharField(max_length=30, null=True)
    senate_file = models.CharField(max_length=30, null=True)
    deputies_header_file = models.CharField(max_length=30, null=True)  # no sé si sirve, si no se saca
    senate_header_file = models.CharField(max_length=30, null=True)
    status = models.CharField(choices=ProjectStatus.choices, max_length=30, null=True)
    source = models.CharField(max_length=100, null=True)

    @property
    def project_id(self):
        return self.deputies_project_id or self.senate_project_id