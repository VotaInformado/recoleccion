# One time command

import pandas as pd
from django.db.models import Q

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.models import LawProject
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        senate_projects_to_correct = LawProject.objects.filter(
            Q(senate_project_id__isnull=False) & (Q(senate_number__isnull=True) | Q(senate_year__isnull=True))
        )
        logger.info(f"senate_projects_to_correct: {senate_projects_to_correct.count()}")
        deputies_projects_to_correct = LawProject.objects.filter(
            Q(deputies_project_id__isnull=False) & (Q(deputies_number__isnull=True) | Q(deputies_year__isnull=True))
        )
        logger.info(f"deputies_projects_to_correct: {deputies_projects_to_correct.count()}")
        combined_projects = senate_projects_to_correct | deputies_projects_to_correct
        senate_projects_to_update, deputies_projects_to_update = [], []
        for project in combined_projects:
            if project.senate_project_id:
                senate_number, senate_source, senate_year = LawProject.split_id(project.senate_project_id)
                project.senate_number = senate_number
                project.senate_source = senate_source
                project.senate_year = senate_year
                senate_projects_to_update.append(project)
            if project.deputies_project_id:
                deputies_number, deputies_source, deputies_year = LawProject.split_id(project.deputies_project_id)
                project.deputies_number = deputies_number
                project.deputies_source = deputies_source
                project.deputies_year = deputies_year
                deputies_projects_to_update.append(project)
        LawProject.objects.bulk_update(senate_projects_to_update, ["senate_number", "senate_source", "senate_year"])
        LawProject.objects.bulk_update(
            deputies_projects_to_update, ["deputies_number", "deputies_source", "deputies_year"]
        )
