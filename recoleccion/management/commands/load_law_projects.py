# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import HCDNLawProjects
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter


class Command(BaseCommand):
    help = "Load laws from the deputy source"

    @transaction.atomic
    def handle(self, *args, **options):
        laws_data = HCDNLawProjects.get_data()
        written_projects = LawProjectsWriter.write(laws_data)
