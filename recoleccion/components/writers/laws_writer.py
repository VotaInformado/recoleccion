from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np

# Project
from recoleccion.models.law import Law
from recoleccion.components.writers import Writer


class LawsWriter(Writer):
    model = Law

    def write(self, data: pd.DataFrame):
        written = []
        for i in data.index:
            row = data.loc[i]
            element = self.update_or_create_element(row)
            written.append(element)
        return written

    def is_valid_date(self, date_str):
        date_format = "%Y-%m-%d"
        try:
            dt.strptime(date_str, date_format)
            return True
        except ValueError:
            return False
        
    def has_initial_file(self, initial_file: str):
        return initial_file and initial_file != "NULL" and not pd.isnull(initial_file)

    def update_or_create_element(self, row: pd.Series):
        publication_date = row["publication_date"] if self.is_valid_date(row["publication_date"]) else None
        vetoed = True if row["veto"] != "NULL" else False
        initial_file = row["initial_file"] if self.has_initial_file(row["initial_file"]) else None
        law_info = {
            "title": row["title"],
            "summary": row["summary"],
            "tags": row["tags"],
            "publication_date": publication_date,
            "associated_decree": row["decree"],
            "vetoed": vetoed,
            "initial_file": initial_file,
        }

        law = Law.objects.update_or_create(
            law_number=row["law_number"],
            defaults=law_info,
        )
        return law
