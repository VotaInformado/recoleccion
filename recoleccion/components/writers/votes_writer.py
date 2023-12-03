from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np
import logging

# Project
from recoleccion.models.linking import DENIED_INDICATOR
from recoleccion.models import Law, LawProject, Party, Person, Vote
from recoleccion.components.writers import Writer
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.vote_choices import VOTE_CHOICE_TRANSLATION
from recoleccion.utils.enums.vote_types import VoteTypes


class VotesWriter(Writer):
    model = Vote

    def __init__(self):
        self.last_day_order = None
        self.last_deputies_project_id = None
        self.last_senate_project_id = None
        self.last_deputies_project = None
        self.last_senate_project = None
        self.logger = logging.getLogger(__name__)

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

    def retrieve_project(self, project_id: str, chamber: str):
        if pd.isnull(project_id) or not project_id:
            return None
        number, year = LawProject.get_project_year_and_number(project_id)
        if chamber == ProjectChambers.DEPUTIES:
            project = LawProject.objects.filter(deputies_year=year, deputies_number=number).first()
            if project:
                self.logger.info(f"Found deputies project with year {year} and number {number}")
        else:
            project = LawProject.objects.filter(senate_year=year, senate_number=number).first()
            if project:
                self.logger.info(f"Found senate project with year {year} and number {number}")
        if not project:
            self.logger.info(f"Project with year {year} and number {number} not found for chamber {chamber}")
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
            person = Person.objects.get(id=row.get("person_id"))
        else:
            row["person_name"] = row.get("name")
            row["person_last_name"] = row.get("last_name")
            person = None
        row = row.drop(["name", "last_name"], errors="ignore")
        return row, person

    def _get_vote_project(self, row: pd.Series, project_id: str, chamber: str) -> pd.Series:
        if not project_id:
            return row, None
        if chamber == ProjectChambers.DEPUTIES:
            row_var = "deputies_project_id"
            last_id_var = "last_deputies_project_id"
            last_project_var = "last_deputies_project"
        else:
            row_var = "senate_project_id"
            last_id_var = "last_senate_project_id"
            last_project_var = "last_senate_project"
        if project_id:
            if project_id == getattr(self, last_id_var):
                self.logger.info(
                    f"Project with deputies id {project_id} coincides, using last project: {getattr(self, last_id_var)}"
                )
                row["project"] = getattr(self, last_project_var)
                return row, getattr(self, last_project_var)
            project = self.retrieve_project(project_id, chamber)
            if not project:
                row["reference"] = row[row_var]
                return row, None
            setattr(self, last_id_var, project_id)
            setattr(self, last_project_var, project)
            row["project"] = project
            return row, project

    def get_vote_project(self, row: pd.Series) -> pd.Series:
        deputies_project_id = row.get("deputies_project_id", None)
        row, project = self._get_vote_project(row, deputies_project_id, ProjectChambers.DEPUTIES)
        if project:
            return row, project
        senate_project_id = row.get("senate_project_id", None)
        row, project = self._get_vote_project(row, senate_project_id, ProjectChambers.SENATORS)
        if project:
            return row, project

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

    def get_existing_vote(self, row, person, law_project, law, reference):
        # If we have a person, we can use it to filter
        # Else, we have to use the name and last name
        if not person:
            vote = Vote.objects.filter(
                person_name=row.get("person_name"),
                person_last_name=row.get("person_last_name"),
                project=law_project,
                law=law,
                reference=reference,
            ).first()
        else:
            vote = Vote.objects.filter(
                person=person,
                project=law_project,
                law=law,
                reference=reference,
            ).first()
        return vote

    def format_vote(self, vote: str) -> str:
        if not vote or vote.title() == "Sin votar":
            return ""
        vote = vote.title().upper()
        return VOTE_CHOICE_TRANSLATION.get(vote, vote)

    def write_vote(self, row: pd.Series, person, law_project, law, reference):
        existing_vote = self.get_existing_vote(row, person, law_project, law, reference)
        row.update({"vote": self.format_vote(row.vote)})
        if existing_vote:
            this_vote_type = row.get("vote_type", None)
            if this_vote_type == VoteTypes.GENERAL:
                existing_vote.update(**row.to_dict())
                vote = existing_vote
                was_created = False
            elif existing_vote.vote_type != VoteTypes.GENERAL:
                # podemos actualizar si el existente no es general
                vote = existing_vote.update(**row.to_dict())
                was_created = False
            else:
                self.logger.info("General vote already exists, not updating")
                vote, was_created = None, False
        else:
            row = row.drop(["index"], errors="ignore")
            vote = Vote.objects.create(**row.to_dict())
            was_created = True
        return vote, was_created

    def update_or_create_element(self, row: pd.Series):
        row = row.dropna()
        row, person = self.clean_person_data(row)
        row, law_project = self.get_vote_project(row)
        row = row.drop(["deputies_project_id", "senate_project_id", "day_order"], errors="ignore")
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

    def update_vote_parties(self, updated_votes: pd.DataFrame):
        """Receives a DF with cols: vote_id, party_id
        Updates only the party_id of the votes with the given vote_id
        """
        votes_with_party = updated_votes[updated_votes["party_id"].notnull()]
        # we keep only the votes that have a party_id
        votes_with_party.loc[votes_with_party["party_id"] == DENIED_INDICATOR, "party_id"] = None
        for i in votes_with_party.index:
            party_id = votes_with_party.loc[i, "party_id"]
            vote_info = votes_with_party.loc[i]
            vote = Vote.objects.get(id=vote_info["record_id"])
            if pd.isna(party_id):
                party = None
            else:
                party = Party.objects.get(id=party_id)
            vote.party = party
            vote.save()
