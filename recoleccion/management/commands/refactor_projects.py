import pandas as pd

# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Project
from recoleccion.models.law_project import LawProject

# Utils
from tqdm import tqdm


class Command(BaseCommand):
    def fix_deputies_id(self, project):
        if project.deputies_project_id is None:
            return
        if project.deputies_year or project.deputies_number or project.deputies_source:
            return
        comps = project.deputies_project_id.split("-")
        source = None
        if len(comps) == 3:
            if project.deputies_project_id.startswith("D"):
                source, num, year = comps
                project.deputies_project_id = f"{num}-{source}-{year}"
            else:
                num, source, year = comps
        if len(comps) == 2:
            num, year = comps
        project.deputies_number = int(num)
        project.deputies_source = source.upper() if source else None
        project.deputies_year = int(year)

    def fix_senate_id(self, project):
        if project.senate_project_id is None:
            return
        if project.senate_year or project.senate_number or project.senate_source:
            return
        project_id = project.senate_project_id.replace("/", "-")
        comps = project_id.split("-")
        source = None
        if len(comps) == 3:
            num, source, year = comps
        if len(comps) == 2:
            num, year = comps
        project.senate_number = int(num)
        project.senate_source = source.upper() if source else None
        project.senate_year = int(year)
        project.senate_project_id = project_id

    def handle(self, *args, **options):
        projects = LawProject.objects.all()
        for project in tqdm(projects):
            try:
                self.fix_deputies_id(project)
                self.fix_senate_id(project)
                project.save()
            except Exception as e:
                print(
                    f"Erorr fixing project id:{project.id}, deputy_id: {project.deputies_project_id}, senate_id: {project.senate_project_id}: {e}"
                )
