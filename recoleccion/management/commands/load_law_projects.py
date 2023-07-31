# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction

# Components
from recoleccion.components.data_sources.law_projects_source import DeputyLawProjects
from recoleccion.components.writers.law_projects_writer import LawProjectsWriter


class Command(BaseCommand):
    help = "Load laws from the deputy source"

    @transaction.atomic
    def handle(self, *args, **options):
        laws_data = DeputyLawProjects.get_data()
        written_projects = LawProjectsWriter.write(laws_data)
