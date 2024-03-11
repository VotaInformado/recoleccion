# Django
from django.db import models

# Project
from recoleccion.models.linking.linking_decision import LinkingDecision


class PartyLinkingDecision(LinkingDecision):
    main_attribute = "party"
    party = models.ForeignKey("Party", on_delete=models.CASCADE, related_name="linking", null=True)
    messy_denomination = models.CharField(max_length=255, null=True, help_text="Messy denomination")

    class Meta:
        unique_together = ("party", "messy_denomination")

    def get_messy_record(self):
        return {"messy_denomination": self.messy_denomination}

    def get_canonical_record(self):
        return {"canonical_denomination": self.party.main_denomination}

    def _update_records(self, records):
        if records:
            records.update(party=self.party)

    def __str__(self):
        if not self.party:
            return f"PartyLinkingDecision ({self.decision}): {self.messy_denomination} - {self.decision}"
        return (
            f"PartyLinkingDecision ({self.decision}):\n"
            + f"Canonical denomination: {self.party.main_denomination}\n"
            + f"Messy denomination: {self.messy_denomination}"
        )
