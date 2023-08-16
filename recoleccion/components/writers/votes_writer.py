from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np

# Project
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.models import Law, LawProject, Person, Vote
from recoleccion.components.writers import Writer
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_types import VoteTypes


class VotesWriter(Writer):
    model = Vote

    def __init__(self):
        self.last_day_order = None
        self.last_project_id = None
        self.last_project = None
        self.logger = CustomLogger(name="Writer", log_file_path="logs/votes_writer.log")

    def write(self, data: pd.DataFrame):
        self.logger.info(f"Received {len(data)} law projects to write...")
        written, updated = [], []
        for i in data.index:
            row = data.loc[i]
            element, was_created = self.update_or_create_element(row)
            if was_created:
                written.append(element)
            else:
                updated.append(element)
        self.logger.info(f"Created {len(written)} {self.model.__name__}s")
        self.logger.info(f"Updated {len(updated)} {self.model.__name__}s")
        return written

    def retrieve_project(self, project_id: str):
        if pd.isnull(project_id) or not project_id:
            return None
        alternative_project_ids = LawProject.get_all_alternative_ids(project_id)
        for alternative_id in alternative_project_ids:
            project = LawProject.objects.filter(deputies_project_id=alternative_id).first()
            if project:
                self.logger.info(f"Found deputies project with id {alternative_id}")
                break
        else:
            for alternative_id in alternative_project_ids:
                project = LawProject.objects.filter(senate_project_id=alternative_id).first()
                if project:
                    self.logger.info(f"Found senate project with id {alternative_id}")
                    break
        if not project:
            self.logger.info(f"Project with ids {','.join(alternative_project_ids)} not found")
        return project

    def retrieve_project_from_day_order(self, day_order: int, chamber: str) -> LawProject:
        if pd.isnull(day_order) or not day_order:
            return None
        if not chamber:
            return None
        if chamber == ProjectChambers.DEPUTIES:
            project = LawProject.objects.filter(deputies_day_order=day_order).first()
        else:
            project = LawProject.objects.filter(senate_day_order=day_order).first()
        if project:
            self.logger.info(f"Found project with day order {day_order}")
        else:
            self.logger.info(f"Project with day order {day_order} not found")
        return project

    def clean_person_data(self, row: pd.Series) -> pd.Series:
        if row.get("person_id"):
            row = row.drop(["name", "last_name"])
            person = Person.objects.get(id=row.get("person_id"))
        else:
            row["person_name"] = row.get("name")
            row["person_last_name"] = row.get("last_name")
            row = row.drop(["name", "last_name"])
            person = None
        return row, person

    def get_vote_project(self, row: pd.Series) -> pd.Series:
        project_id = row.get("project_id", None)
        if project_id:
            if project_id == self.last_project_id:
                self.logger.info(
                    f"Project id {project_id} coincides, using last project: {self.last_project.project_id}"
                )
                row["project"] = self.last_project
                return row, self.last_project
            project = self.retrieve_project(project_id)
            if not project:
                row["reference"] = row["project_id"]
                return row, None
            self.last_project_id = project_id
            self.last_project = project
            row["project"] = project
            return row, project
        else:  # no hay project_id, hay que usar day_order
            day_order = row.get("day_order", None)
            if not day_order:
                return row, None
            if day_order == self.last_day_order:
                self.logger.info(f"Day order {day_order} coincides, using last project: {self.last_project.project_id}")
                row["project"] = self.last_project
                return row, self.last_project
            project = self.retrieve_project_from_day_order(day_order, row["chamber"])
            if not project:
                row["reference"] = row["day_order"]
                return row, None
            self.last_day_order = day_order
            self.last_project = project
            row["project"] = project
            return row, project

    def get_vote_law(self, row: pd.Series) -> pd.Series:
        law_number = row.get("law", None)
        law = Law.objects.filter(law_number=law_number).first()
        if not law:
            row["reference"] = row["law"]
            row = row.drop(["law"], errors="ignore")
            self.logger.warning(f"Law with number {law_number} not found")
            return row, None
        row["law"] = law
        return row, law

    def write_vote(self, row: pd.Series, person, law_project, law, reference):
        existing_vote = Vote.objects.filter(
            person=person,
            person_name=row.get("person_name"),
            person_last_name=row.get("person_last_name"),
            project=law_project,
            law=law,
            reference=reference,
        ).first()
        if existing_vote:
            this_vote_type = row.get("vote_type", None)
            if this_vote_type == VoteTypes.GENERAL:
                existing_vote.update(**row.to_dict())
                vote = existing_vote
                was_created = False
            elif existing_vote.vote_type != VoteTypes.GENERAL:  # podemos actualizar si el existente no es general
                vote = existing_vote.update(**row.to_dict())
                was_created = False
            else:
                self.logger.info("General vote already exists, not updating")
                vote, was_created = None, False
        else:
            vote = Vote.objects.create(**row.to_dict())
            was_created = True
        return vote, was_created

    def update_or_create_element(self, row: pd.Series):
        row = row.dropna()
        row, person = self.clean_person_data(row)
        row, law_project = self.get_vote_project(row)
        row = row.drop(["project_id", "day_order"], errors="ignore")
        if row.get("law", None) is not None:
            row, law = self.get_vote_law(row)
        else:
            law = None
        reference = row.get("reference", None)

        vote, was_created = self.write_vote(
            row,
            person,
            law_project,
            law,
            reference,
        )
        return vote, was_created
