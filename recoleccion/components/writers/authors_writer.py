from django.db.models import Q
import pandas as pd
from datetime import datetime as dt

# Project
from recoleccion.models import Authorship, LawProject, Person
from recoleccion.components.writers import Writer
from recoleccion.models.linking import DENIED_INDICATOR


class AuthorsWriter(Writer):
    model = Authorship

    @classmethod
    def existing_data(cls, data_source: str) -> bool:
        return cls.model.objects.filter(source=data_source).exists()

    @classmethod
    def write(cls, data: pd.DataFrame):
        data_source = data["source"].iloc[0]
        if cls.existing_data(data_source):
            cls.logger.info("There are already authors in the database, writing with existing data...")
            cls._write_with_existing_data(data)
        else:
            cls.logger.info("There are no authors in the database, writing from scratch...")
            cls._write_from_scratch(data)

    @classmethod
    def _get_authorship_from_row(cls, row: pd.Series) -> Authorship:
        row = row.drop(["index"], errors="ignore")
        row = cls._format_row(row)
        row_data = row.to_dict()
        authorship = Authorship(**row_data)
        return authorship

    @classmethod
    def _write_from_scratch(cls, data: pd.DataFrame):
        """
        Will be used only when there is not a single author in the database
        It will optimize the process by not checking for duplicates and performing bulk inserts
        """
        BATCH_SIZE = 500
        data_to_write = []
        for index, row in data.iterrows():
            authorship: Authorship = cls._get_authorship_from_row(row)
            data_to_write.append(authorship)
            if len(data_to_write) == BATCH_SIZE:
                cls.model.objects.bulk_create(data_to_write, ignore_conflicts=True)
                data_to_write = []
        if data_to_write:  # if there are still elements to write
            cls.model.objects.bulk_create(data_to_write, ignore_conflicts=True)

    @classmethod
    def _write_with_existing_data(cls, data: pd.DataFrame):
        """
        Will be used when there are already authors in the database
        It will be the regular way of writing authors, like other objects
        """
        written = updated = 0
        cls.associated_projects = 0
        for i in data.index:
            row = data.loc[i]
            element, was_created = cls.update_or_create_element(row)
            if was_created:
                written += 1
            else:
                updated += 1
        cls.logger.info(f"{written} authors were created and {updated} were updated")

    @classmethod
    def get_project(cls, row: pd.Series):
        deputies_project_id = row.get("deputies_project_id", None)
        if deputies_project_id:
            number, year = LawProject.get_project_year_and_number(deputies_project_id)
            law_project = LawProject.objects.filter(deputies_year=year, deputies_number=number).first()
            if law_project:
                cls.logger.info(f"Law project with id {deputies_project_id} found")
            else:
                cls.logger.info(f"Law project with deputies year {year} and number {number} not found...")
            return law_project
        senate_project_id = row.get("senate_project_id", None)
        if senate_project_id:
            senate_project_id = senate_project_id.replace("/", "-")  # some ids have a slash instead of a dash
            number, year = LawProject.get_project_year_and_number(senate_project_id)
            law_project = LawProject.objects.filter(senate_year=year, senate_number=number).first()
            if law_project:
                cls.logger.info(f"Law project with id {senate_project_id} found")
            else:
                cls.logger.info(f"Law project with senate year {year} and number {number} not found...")
            return law_project
        return None

    @classmethod
    def _format_row(cls, row: pd.Series) -> pd.Series:
        """
        Formats the row so that it can be correctly inserted into the database
        """
        row = row.dropna()
        if not row.get("deputies_project_id", None) and not row.get("senate_project_id", None):
            cls.logger.info("No project id found in row, skipping...")
            return None, False
        project = cls.get_project(row)
        if project:
            row["project"] = project
        else:
            row["reference"] = row.get("deputies_project_id", row.get("senate_project_id"))
        row = row.drop(["deputies_project_id", "senate_project_id"], errors="ignore")
        row = row.rename({"name": "person_name", "last_name": "person_last_name"})
        return row

    @classmethod
    def update_or_create_element(cls, row: pd.Series):
        row = row.drop(["index"], errors="ignore")
        row = cls._format_row(row)
        project = row.get("project")
        reference = row.get("reference")
        person = Person.objects.get(id=row["person_id"]) if row.get("person_id") else None
        if person:
            return Authorship.objects.update_or_create(
                project=project,
                person=person,
                reference=reference,
                defaults=row.to_dict(),
            )
        else:
            return Authorship.objects.update_or_create(
                project=project,
                reference=reference,
                person_name=row["person_name"],
                person_last_name=row["person_last_name"],
                defaults=row.to_dict(),
            )
