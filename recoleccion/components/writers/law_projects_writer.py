from django.db.models import Q
import pandas as pd
from datetime import datetime as dt
import numpy as np

# Project
from recoleccion.models import LawProject
from recoleccion.components.writers import Writer
from recoleccion.models.law import Law


class LawProjectsWriter(Writer):
    model = LawProject

    @classmethod
    def write(cls, data: pd.DataFrame):
        cls.logger.info(f"Received {len(data)} law projects to write...")
        written, updated = [], []
        for i in data.index:
            row = data.loc[i]
            element, was_created = cls.update_or_create_element(row)
            if was_created:
                cls.logger.info(f"Created law project {element.project_id}")
                written.append(element)
            elif element:
                cls.logger.info(f"Updated law project {element.project_id}")
                updated.append(element)
        cls.logger.info(f"Created {len(written)} law projects")
        cls.logger.info(f"Updated {len(updated)} law projects")
        return written

    @classmethod
    def update_law(cls, law_number: str, law_project: LawProject):
        law = Law.objects.filter(law_number=law_number).first()
        if law:
            law.law_project = law_project
            law.save()
        else:
            cls.logger.warning(
                f"Law with number {law_number} not found, project {law_project.project_id} not associated"
            )

    @classmethod
    def update_or_create_element(cls, row: pd.Series):
        row = row.dropna()
        deputies_project_id = row.get("deputies_project_id", None)
        senate_project_id = row.get("senate_project_id", None)
        law = row.get("law", None)
        row = row.drop("law", errors="ignore")
        try:
            if row.get("origin_chamber", None) == "Diputados":
                law_project, was_created = LawProject.objects.update_or_create(
                    deputies_project_id=deputies_project_id,
                    defaults=row.to_dict(),
                )
            else:
                law_project, was_created = LawProject.objects.update_or_create(
                    senate_project_id=senate_project_id,
                    defaults=row.to_dict(),
                )
            if law:
                cls.update_law(law, law_project)
        except Exception as e:
            project_id = deputies_project_id or senate_project_id
            cls.logger.warning(f"An error occurred while updating or creating law project with id {project_id}: {e}")
            return None, False
        return law_project, was_created

    @classmethod
    def update_day_orders(cls, data: pd.DataFrame):
        cls.logger.info(f"Received {len(data)} day orders to update...")
        updated, not_found = [], []
        for i in data.index:
            row = data.loc[i]
            project_id = row.get("project_id")
            day_order = row.get("day_order")
            project = LawProject.objects.filter(deputies_project_id=project_id).first()
            if project:
                project.deputies_day_order = day_order
                project.save()
                cls.logger.info(f"Updated day order for project {project_id}")
                updated.append(project)
            else:
                cls.logger.warning(f"Project {project_id} not found, day order {day_order} not updated")
                not_found.append(project_id)
        cls.logger.info(f"Updated {len(updated)} day orders")
        cls.logger.info(f"{len(not_found)} day orders not found")
