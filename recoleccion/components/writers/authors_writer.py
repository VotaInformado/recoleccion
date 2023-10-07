from django.db.models import Q
import pandas as pd
from datetime import datetime as dt

# Project
from recoleccion.models import Authorship, LawProject, Party, Person
from recoleccion.components.writers import Writer
from recoleccion.models.linking import DENIED_INDICATOR


class AuthorsWriter(Writer):
    model = Authorship

    @classmethod
    def write(cls, data: pd.DataFrame):
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
                cls.logger.info(f"Law project with year {year} and number {number} not found...")
            return law_project
        senate_project_id = row.get("senate_project_id", None)
        if senate_project_id:
            senate_project_id = senate_project_id.replace("/", "-")  # some ids have a slash instead of a dash
            number, year = LawProject.get_project_year_and_number(senate_project_id)
            law_project = LawProject.objects.filter(senate_year=year, senate_number=number).first()
            if law_project:
                cls.logger.info(f"Law project with id {senate_project_id} found")
            else:
                cls.logger.info(f"Law project with year {year} and number {number} not found...")
            return law_project
        return None

    @classmethod
    def update_or_create_element(cls, row: pd.Series):
        row = row.dropna()
        if not row.get("deputies_project_id", None) and not row.get("senate_project_id", None):
            cls.logger.info("No project id found in row, skipping...")
            return None, False
        project = cls.get_project(row)
        if project:
            row["law_project"] = project
        else:
            row["reference"] = row.get("deputies_project_id", row.get("senate_project_id"))
        row = row.drop(["deputies_project_id", "senate_project_id"], errors="ignore")
        row = row.rename({"name": "person_name", "last_name": "person_last_name"})
        reference = row.get("reference", None)
        person = Person.objects.get(id=row["person_id"]) if row.get("person_id", None) else None

        if person:
            return Authorship.objects.update_or_create(
                law_project=project,
                person=person,
                reference=reference,
                defaults=row.to_dict(),
            )
        else:
            return Authorship.objects.update_or_create(
                law_project=project,
                reference=reference,
                person_name=row["person_name"],
                person_last_name=row["person_last_name"],
                defaults=row.to_dict(),
            )

    def update_authors_parties(self, updated_authors: pd.DataFrame):
        """Receives a DF with cols: record_id (author_id), party_id
        Updates only the party_id of the authors with the given record_id
        """
        authors_with_party = updated_authors[updated_authors["party_id"].notnull()]
        # we make sure to discard unlinked authors
        authors_with_party = authors_with_party[authors_with_party["party_id"] != DENIED_INDICATOR]
        # we must consider only approved linking decisions
        for i in authors_with_party.index:
            author_info = updated_authors.loc[i]
            author = Authorship.objects.get(id=author_info["record_id"])
            party = Party.objects.get(id=author_info["party_id"])
            author.party = party
            author.save()
