# Django
from django.db import models

from recoleccion.models.linking.linking_decision import LinkingDecision


class PersonLinkingDecision(LinkingDecision):
    main_attribute = "person"
    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="linking", null=True)
    messy_name = models.CharField(max_length=255, null=True, help_text="Messy full name")

    class Meta:
        unique_together = ("person", "messy_name")

    def get_messy_record(self):
        return {"messy_name": self.messy_name}

    def get_canonical_record(self):
        return {"canonical_name": self.person.full_name}

    def __str__(self):
        if not self.person:
            return f"PersonLinkingDecision ({self.decision}): {self.messy_name} - {self.decision}"
        return (
            f"PersonLinkingDecision ({self.decision}):\n"
            + f"Canonical name: {self.person.formal_full_name}\n"
            + f"Messy name: {self.messy_name}"
        )
