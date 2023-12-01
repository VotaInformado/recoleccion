# Django
from django.db import models

# Base model
from recoleccion.models.base import BaseModel
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


class LinkingDecision(BaseModel):
    decision = models.CharField(
        choices=LinkingDecisions.choices, max_length=10, null=True, default=LinkingDecisions.PENDING
    )

    def is_approved(self):
        return self.decision == LinkingDecisions.APPROVED

    def is_denied(self):
        return self.decision == LinkingDecisions.DENIED

    def is_pending(self):
        return self.decision == LinkingDecisions.PENDING
