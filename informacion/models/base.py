import uuid

# Django
from django.db import models

class BaseModel(models.Model):

    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        'created at',
        auto_now_add=True,
        help_text='Date time on which the object was created.'
    )
    modified_at = models.DateTimeField(
        'updated at',
        auto_now=True,
        help_text='Date time on which the object was last modified.'
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
