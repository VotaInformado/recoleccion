from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np

# Project
from recoleccion.models.law import Law
from recoleccion.components.writers import Writer
from recoleccion.models.law_project import LawProject


class LawsWriter(Writer):
    model = Law

    def write(self, data: pd.DataFrame):
        written = updated = 0
        self.associated_projects = 0
        for i in data.index:
            row = data.loc[i]
            element, was_created = self.update_or_create_element(row)
            if was_created:
                written += 1
            else:
                updated += 1
        self.logger.info(f"{written} laws were created and {updated} were updated")
        self.logger.info(f"{self.associated_projects} laws were associated to projects")

    def is_valid_date(self, date_str):
        date_format = "%Y-%m-%d"
        try:
            dt.strptime(date_str, date_format)
            return True
        except ValueError:
            return False

    def has_initial_file(self, initial_file: str):
        return initial_file and initial_file != "NULL" and not pd.isnull(initial_file)

    def associate_project(self, row: pd.Series):
        project_id = row.get("project_id", None)
        if not project_id:
            row["project_id"] = None
            return row
        project = LawProject.objects.filter(Q(deputies_project_id=project_id) | Q(senate_project_id=project_id)).first()
        row["associated_project"] = project
        if project:
            self.associated_projects += 1

    def update_or_create_element(self, row: pd.Series):
        row = row.dropna()
        row["vetoed"] = True if row["veto"] != "NULL" else False
        self.associate_project(row)
        row.pop("veto")
        if row["publication_date"] == "NUL":
            row["publication_date"] = None
        return Law.objects.update_or_create(
            law_number=row["law_number"],
            defaults=row.to_dict(),
        )
