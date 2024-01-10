import re
from django.db import models

# Base model
from recoleccion.models.base import BaseModel


class StoredNews(BaseModel):
    title = models.TextField(null=True)
    link = models.CharField(max_length=1000, null=True)
    video_url = models.CharField(max_length=1000, null=True)
    image_url = models.CharField(max_length=1000, null=True)
    pubDate = models.DateTimeField(null=True)
    description = models.TextField(null=True)
    source_id = models.CharField(max_length=100, null=True)  # nos sirve para saber qué fuentes filtrar
