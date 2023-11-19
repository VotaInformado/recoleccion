import pandas as pd


# Project
from recoleccion.models import LawProject
from recoleccion.components.writers import Writer
from recoleccion.models.law import Law
from recoleccion.utils.enums.project_chambers import ProjectChambers


class LawProjectsWriter(Writer):
    model = LawProject

    @classmethod
    def split_id(self, project_id: str):
        if project_id is None:
            return None, None, None
        comps = project_id.split("-")
        if len(comps) == 3:
            num, source, year = comps
        if len(comps) == 2:
            num, year = comps
            source = None
        num = int(num)
        source = source.upper() if source else None
        year = int(year)
        return num, source, year

    @classmethod
    def format_year(cls, project_id: str):
        if not project_id:
            return None
        project_year = project_id.split("/")[-1]
        year = int(project_year)
        if year < 50:
            return year + 2000
        if year < 100:
            return year + 1900

        return int(project_year)

    @classmethod
    def write(cls, data: pd.DataFrame, update_existing=True):
        cls.logger.info(f"Received {len(data)} law projects to write...")
        written, updated = [], []
        for i in data.index:
            row = data.loc[i]
            element, was_created = cls.update_or_create_element(row, update_existing)
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
    def update_or_create_element(cls, row: pd.Series, update_existing: bool):
        row = row.dropna()
        deputies_project_id = row.get("deputies_project_id", None)
        senate_project_id = row.get("senate_project_id", None)
        senate_project_id = (
            senate_project_id.replace("/", "-") if senate_project_id else None
        )
        row[
            "senate_project_id"
        ] = senate_project_id  # fix for senate projects with wrong format
        law = row.get("law", None)
        row = row.drop("law", errors="ignore")
        deputies_number, deputies_source, deputies_year = cls.split_id(
            deputies_project_id
        )
        deputies_year = cls.format_year(deputies_project_id)
        senate_number, senate_source, senate_year = cls.split_id(senate_project_id)
        senate_year = cls.format_year(senate_project_id)
        row.update(
            {
                "deputies_project_id": f"{deputies_number}-{deputies_source}-{deputies_year}",
                "senate_project_id": f"{senate_number}-{senate_source}-{senate_year}",
                "deputies_number": deputies_number,
                "deputies_source": deputies_source,
                "deputies_year": deputies_year,
                "senate_number": senate_number,
                "senate_source": senate_source,
                "senate_year": senate_year,
            }
        )
        try:
            source = row.get("source", "")
            if "senado" in source.lower():
                if not update_existing:
                    law_project = LawProject.objects.filter(
                        senate_number=senate_number, senate_year=senate_year
                    ).first()
                    if law_project:
                        cls.logger.info(
                            f"Law project {law_project.project_id} already exists, skipping..."
                        )
                        return law_project, False
                    else:
                        law_project = LawProject.objects.create(**row.to_dict())
                        return law_project, True
                else:
                    law_project, was_created = LawProject.objects.update_or_create(
                        senate_year=senate_year,
                        senate_source=senate_source,
                        senate_number=senate_number,
                        defaults=row.to_dict(),
                    )
            else:
                law_project, was_created = LawProject.objects.update_or_create(
                    deputies_year=deputies_year,
                    deputies_source=deputies_source,
                    deputies_number=deputies_number,
                    defaults=row.to_dict(),
                )
            if law:
                cls.update_law(law, law_project)
        except Exception as e:
            project_id = deputies_project_id or senate_project_id
            cls.logger.warning(
                f"An error occurred while updating or creating law project with id {project_id}: {e}"
            )
        return law_project, was_created

    @classmethod
    def update_day_orders(cls, data: pd.DataFrame):
        cls.logger.info(f"Received {len(data)} day orders to update...")
        updated, not_found = [], []
        for i in data.index:
            row = data.loc[i]
            project_id = row.get("project_id")
            day_order = row.get("day_order")
            deputies_number, deputies_source, deputies_year = cls.split_id(project_id)
            project = LawProject.objects.filter(
                deputies_number=deputies_number, deputies_year=deputies_year
            ).first()
            if project:
                project.deputies_day_order = day_order
                project.save()
                cls.logger.info(f"Updated day order for project {project_id}")
                updated.append(project)
            else:
                cls.logger.warning(
                    f"Project {project_id} not found, day order {day_order} not updated"
                )
                not_found.append(project_id)
        cls.logger.info(f"Updated {len(updated)} day orders")
        cls.logger.info(f"{len(not_found)} day orders not found")
