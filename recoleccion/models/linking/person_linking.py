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
