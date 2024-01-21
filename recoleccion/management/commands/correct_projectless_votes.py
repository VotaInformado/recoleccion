# One time command# One time command
from django.core.management.base import BaseCommand
from django.db import IntegrityError
import logging
from tqdm import tqdm

# Project
from recoleccion.models import LawProject, Vote

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        votes_without_project = Vote.objects.filter(project_id=None)
        total_updated = total_deleted = total_not_found = 0
        not_found_references = set()
        for i, vote in enumerate(tqdm(votes_without_project)):
            if i > 0 and i % 500 == 0:
                logger.info(f"Votes updated (out of {i}): {total_updated}")
                logger.info(f"Votes deleted (out of {i}): {total_deleted}")
                logger.info(f"Votes not found (out of {i}): {total_not_found}")
            if vote.reference in not_found_references:
                total_not_found += 1
                continue
            number, chamber, year = LawProject.split_id(vote.reference)
            if not number and not year:  # invalid reference format
                total_not_found += 1
                not_found_references.add(vote.reference)
                continue
            if vote.source == "Senado":
                if chamber:
                    project = LawProject.objects.filter(senate_number=number, senate_year=year, senate_source=chamber).first()
                else:
                    project = LawProject.objects.filter(senate_number=number, senate_year=year).first()
            else:  # Diputados
                if chamber:
                    project = LawProject.objects.filter(
                        deputies_number=number, deputies_year=year, deputies_source=chamber
                    ).first()
                else:
                    project = LawProject.objects.filter(deputies_number=number, deputies_year=year).first()
            if project:
                vote.project = project
                try:
                    vote.save()
                    total_updated += 1
                except IntegrityError:
                    vote.delete()
                    total_deleted += 1
            else:
                not_found_references.add(vote.reference)
                total_not_found += 1

        logger.info(f"Total votes updated: {total_updated}")
        logger.info(f"Total votes deleted: {total_deleted}")
        logger.info(f"Total votes not found: {total_not_found}")
