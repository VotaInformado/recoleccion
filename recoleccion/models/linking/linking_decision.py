# Django
from django.db import models
from typing import List
from django.db.utils import IntegrityError
from recoleccion.models.affidavit_entry import AffidavitEntry

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

    def _get_related_records(self):
        related_votes = Vote.objects.filter(linking_id=self.uuid).all()
        related_authors = Authorship.objects.filter(linking_id=self.uuid).all()
        related_senate_seats = SenateSeat.objects.filter(linking_id=self.uuid).all()
        related_deputy_seats = DeputySeat.objects.filter(linking_id=self.uuid).all()
        all_records = (
            list(related_votes) + list(related_authors) + list(related_senate_seats) + list(related_deputy_seats)
        )
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
        related_affidavits = AffidavitEntry.objects.filter(linking_id=self.uuid).all()
        self._update_records(related_affidavits)
        total_updated = (
            related_votes.count()
            + related_authors.count()
            + related_senate_seats.count()
            + related_deputy_seats.count()
            + related_affidavits.count()
        )
        return total_updated

    def unlink_related_records(self):
        related_votes = Vote.objects.filter(linking_id=self.uuid).all()
        related_votes.update(linking_id=None)
        related_authors = Authorship.objects.filter(linking_id=self.uuid).all()
        related_authors.update(linking_id=None)
        related_senate_seats = SenateSeat.objects.filter(linking_id=self.uuid).all()
        related_senate_seats.update(linking_id=None)
        related_deputy_seats = DeputySeat.objects.filter(linking_id=self.uuid).all()
        related_deputy_seats.update(linking_id=None)
        related_affidavits = AffidavitEntry.objects.filter(linking_id=self.uuid).all()
        related_affidavits.update(linking_id=None)
        total_updated = (
            related_votes.count()
            + related_authors.count()
            + related_senate_seats.count()
            + related_deputy_seats.count()
            + related_affidavits.count()
        )
        return total_updated

    def _update_records_individually(self, records: models.QuerySet):
        main_attribute = self.main_attribute
        main_instance = getattr(self, main_attribute)
        for record in records:
            setattr(record, main_attribute, main_instance)
            try:
                record.save()
            except IntegrityError as e:
                self.logger.info(f"Error updating record {record.id}: {e}")
                self.logger.info("The record is duplicated, deleting it...")
                record.delete()

    def _update_records(self, records: models.QuerySet):
        main_attribute = self.main_attribute
        main_instance = getattr(self, main_attribute)
        update_data = {main_attribute: main_instance}
        try:
            records.update(**update_data)
        except IntegrityError as e:
            self.logger.warning(f"Error updating records: {e}")
            self.logger.info("Updating records one by one...")
            self._update_records_individually(records)
