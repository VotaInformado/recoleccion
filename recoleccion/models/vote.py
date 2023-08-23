# Django
from django.db import models, IntegrityError

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_choices import VoteChoices
from recoleccion.utils.enums.vote_types import VoteTypes


class Vote(BaseModel):
    chamber = models.CharField(choices=ProjectChambers.choices, max_length=10)
    date = models.DateField(null=True)
    person = models.ForeignKey("Person", on_delete=models.CASCADE, null=True, related_name="votes")
    person_name = models.CharField(max_length=100, null=True)  # only in case of not finding the person
    person_last_name = models.CharField(max_length=100, null=True)  # only in case of not finding the person
    party = models.CharField(max_length=200, null=True)
    province = models.CharField(max_length=200, null=True)
    vote = models.CharField(choices=VoteChoices.choices, max_length=15)
    project = models.ForeignKey("LawProject", on_delete=models.CASCADE, null=True, related_name="votes")
    law = models.ForeignKey("Law", on_delete=models.CASCADE, null=True, related_name="votes")
    reference = models.CharField(
        max_length=200, null=True, help_text="Reference in case of not finding the project or law"
    )
    reference_description = models.TextField(null=True)
    source = models.CharField(max_length=100, null=True)
    vote_type = models.CharField(choices=VoteTypes.choices, max_length=10, default=VoteTypes.OTHER)

    def save(self, *args, **kwargs):
        # Manual check is necessary because unique_together does not work with null values
        if self._already_exists():
            chamber = self.chamber
            person_id = self.person.pk if self.person else ""
            project_id = self.project.pk if self.project else ""
            raise IntegrityError(
                f"Unique constraint violated: (chamber: {chamber}, person_id: {person_id}, project_id: {project_id})"
            )
        else:
            super().save(*args, **kwargs)

    def _already_exists(self):
        if not self.law and not self.project and not self.reference:
            return False  # no way to check
        if not self.person:
            return (
                Vote.objects.filter(
                    chamber=self.chamber,
                    person_name=self.person_name,
                    person_last_name=self.person_last_name,
                    project=self.project,
                    law=self.law,
                    reference=self.reference,
                )
                .exclude(pk=self.pk)  # necessary for update
                .exists()
            )
        return (
            Vote.objects.filter(
                chamber=self.chamber,
                person=self.person,
                project=self.project,
                law=self.law,
                reference=self.reference,
            )
            .exclude(pk=self.pk)  # necessary for update
            .exists()
        )
