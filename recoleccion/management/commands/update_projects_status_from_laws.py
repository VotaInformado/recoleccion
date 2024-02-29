from django.core.management.base import BaseCommand
import logging

# Project
from recoleccion.models import Law, LawProject
from recoleccion.utils.enums.project_status import ProjectStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # we get all law_projects from laws
        approved_project_ids = Law.objects.all().values_list("associated_project", flat=True)
        law_projects = LawProject.objects.filter(id__in=approved_project_ids)
        law_projects.update(status=ProjectStatus.APPROVED)
        logger.info(f"Updated {law_projects.count()} projects to {ProjectStatus.APPROVED} status")
