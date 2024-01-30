import pandas as pd
from django.db import IntegrityError
from django.core.management.base import BaseCommand
import logging

# Components
from recoleccion.models import (
    Authorship,
    DeputySeat,
    Person,
    PersonLinkingDecision,
    SenateSeat,
    Vote,
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Merges two legislators into one, including all related objects"

    def add_arguments(self, parser):
        parser.add_argument("--super-legislator-id", type=int)
        parser.add_argument("--sub-legislator-id", type=int)

    def update_object(self, model, new_legislator):
        try:
            model.person = new_legislator
            model.save()
            self.updated += 1
        except IntegrityError:
            model.delete()
            self.unable_to_save += 1

    def update_objects(self, objects, new_legislator):
        for obj in objects:
            self.update_object(obj, new_legislator)

    def handle(self, *args, **options):
        self.updated = self.unable_to_save = 0
        super_legislator = Person.objects.get(id=options["super_legislator_id"])
        sub_legislator = Person.objects.get(id=options["sub_legislator_id"])
        logger.info(f"Super legislator: {super_legislator.full_name}")
        logger.info(f"Sub legislator: {sub_legislator.full_name}")
        sub_legislator_senate_seats = list(SenateSeat.objects.filter(person=sub_legislator).all())
        sub_legislator_deputy_seats = list(DeputySeat.objects.filter(person=sub_legislator).all())
        sub_legislator_votes = list(Vote.objects.filter(person=sub_legislator).all())
        sub_legislator_autorships = list(Authorship.objects.filter(person=sub_legislator).all())
        sub_legislator_linking_decisions = list(PersonLinkingDecision.objects.filter(person=sub_legislator).all())
        all_objects = (
            sub_legislator_senate_seats
            + sub_legislator_deputy_seats
            + sub_legislator_votes
            + sub_legislator_autorships
            + sub_legislator_linking_decisions
        )
        confirmation = input(f"Confirm the update of {len(all_objects)} objects? y/n: ") == "y"
        if confirmation:
            self.update_objects(all_objects, super_legislator)
            logger.info(f"Updated {self.updated} objects")
            sub_legislator.delete()
            logger.info(f"Deleted legislator: {sub_legislator.full_name} with id {sub_legislator.id}")
        else:
            logger.info("Aborting...")
