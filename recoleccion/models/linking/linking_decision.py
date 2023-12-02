# Django
from django.db import models

# Project
from recoleccion.models.base import BaseModel
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions
from recoleccion.models.vote import Vote
from recoleccion.models.authorship import Authorship
from recoleccion.models.senate_seat import SenateSeat
from recoleccion.models.deputy_seat import DeputySeat


class LinkingDecision(BaseModel):
    class Meta:
        abstract = True

    decision = models.CharField(
        choices=LinkingDecisionOptions.choices, max_length=10, null=True, default=LinkingDecisionOptions.PENDING
    )

    def is_approved(self):
        return self.decision == LinkingDecisionOptions.APPROVED

    def is_denied(self):
        return self.decision == LinkingDecisionOptions.DENIED

    def is_pending(self):
        return self.decision == LinkingDecisionOptions.PENDING

    def get_messy_record(self) -> dict:
        raise NotImplementedError

    def get_canonical_record(self) -> dict:
        raise NotImplementedError

    def _update_records(self, records):
        raise NotImplementedError

    def _get_related_records(self):
        related_votes = Vote.objects.filter(linking_id=self.id).all()
        related_authors = Authorship.objects.filter(linking_id=self.id).all()
        related_senate_seats = SenateSeat.objects.filter(linking_id=self.id).all()
        related_deputy_seats = DeputySeat.objects.filter(linking_id=self.id).all()
        all_records = related_votes | related_authors | related_senate_seats | related_deputy_seats
        return all_records

    def update_related_records(self):
        related_votes = Vote.objects.filter(linking_id=self.uuid).all()
        self._update_records(related_votes)
        related_authors = Authorship.objects.filter(linking_id=self.uuid).all()
        self._update_records(related_authors)
        related_senate_seats = SenateSeat.objects.filter(linking_id=self.uuid).all()
        self._update_records(related_senate_seats)
        related_deputy_seats = DeputySeat.objects.filter(linking_id=self.uuid).all()
        self._update_records(related_deputy_seats)

    def unlink_related_records(self):
        related_votes = Vote.objects.filter(linking_id=self.uuid).all()
        related_votes.update(linking_id=None)
        related_authors = Authorship.objects.filter(linking_id=self.uuid).all()
        related_authors.update(linking_id=None)
        related_senate_seats = SenateSeat.objects.filter(linking_id=self.uuid).all()
        related_senate_seats.update(linking_id=None)
        related_deputy_seats = DeputySeat.objects.filter(linking_id=self.uuid).all()
        related_deputy_seats.update(linking_id=None)
