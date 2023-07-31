import uuid

# Django
from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True
        app_label = "recoleccion"

    created_at = models.DateTimeField(
        "created at", auto_now_add=True, help_text="Date time on which the object was created."
    )
    modified_at = models.DateTimeField(
        "updated at", auto_now=True, help_text="Date time on which the object was last modified."
    )
    id = models.AutoField(primary_key=True, editable=False, serialize=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    

    def __str__(self):
        return f"{self.__class__.__name__}\n{self.__dict__}"
    
    @classmethod
    def update_or_raise(cls, **kwargs):
        return cls.update(raise_if_not_found=True, **kwargs)

    @classmethod
    def update(cls, raise_if_not_found=False, **kwargs):
        id = kwargs.pop("id", None) or kwargs.pop("pk", None)
        if id:
            instance = cls.objects.filter(id=id).first()
        else:
            if cls._meta.unique_together:
                unique_fields = cls._meta.unique_together[0]
                filter_kwargs = {field: kwargs[field] for field in unique_fields}
                instance = cls.objects.filter(**filter_kwargs).first()
            else:
                instance = None
        if not instance:
            if raise_if_not_found:
                raise Exception(f"Instance of {cls.__name__} not found")
            return None
        return instance._update(**kwargs)

    def _update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()
        return self