from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np

# Project
from recoleccion.models import LawProject, Person, Vote
from recoleccion.components.writers import Writer


class VotesWriter(Writer):
    model = Vote

    @classmethod
    def write(cls, data: pd.DataFrame):
        cls.logger.info(f"Received {len(data)} law projects to write...")
        written, updated = [], []
        for i in data.index:
            row = data.loc[i]
            element, was_created = cls.update_or_create_element(row)
            if was_created:
                written.append(element)
            else:
                updated.append(element)
        cls.logger.info(f"Created {len(written)} {cls.model.__name__}s")
        cls.logger.info(f"Updated {len(updated)} {cls.model.__name__}s")
        return written

    @classmethod
    def get_vote_project(cls, project_id: str):
        # TODO: nombres alternativos de proyecto
        if pd.isnull(project_id) or not project_id:
            return None
        project = LawProject.objects.filter(deputies_project_id=project_id).first()
        if project:
            cls.logger.info(f"Found deputies project with id {project_id}")
        else:
            project = LawProject.objects.filter(senate_project_id=project_id).first()
            if project:
                cls.logger.info(f"Found senate project with id {project_id}")
            else:
                cls.logger.info(f"Project with id {project_id} not found")
        return project

    @classmethod
    def clean_person_data(cls, row: pd.Series) -> pd.Series:
        if row.get("person_id"):
            row = row.drop(["name", "last_name"])
            person = Person.objects.get(id=row.get("person_id"))
        else:
            row["person_name"] = row.get("name")
            row["person_last_name"] = row.get("last_name")
            row = row.drop(["name", "last_name"])
            person = None
        return row, person

    @classmethod
    def clean_vote_project(cls, row: pd.Series) -> pd.Series:
        law_project = cls.get_vote_project(row.get("project_id"))
        if law_project:
            row["project"] = law_project
            row.drop("reference_description", inplace=True)
        else:
            row["reference"] = row.get("project_id")
        row = row.drop("project_id", errors="ignore")
        return row, law_project

    @classmethod
    def update_or_create_element(cls, row: pd.Series):
        row = row.dropna()
        row, person = cls.clean_person_data(row)
        row, law_project = cls.clean_vote_project(row)

        vote, was_created = Vote.objects.update_or_create(
            person=person,
            person_name=row.get("person_name"),
            person_last_name=row.get("person_last_name"),
            project=law_project,
            reference=row.get("reference"),
            defaults=row.to_dict(),
        )
        return vote, was_created
