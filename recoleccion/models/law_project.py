import re
from django.db import models

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.project_status import ProjectStatus
from recoleccion.components.services.text_summarizer import TextSummarizer
from recoleccion.exceptions.custom import EmptyText, ProjectOriginFileConflict


class LawProject(BaseModel):
    deputies_project_id = models.CharField(max_length=30, null=True)
    senate_project_id = models.CharField(max_length=30, null=True)
    deputies_number = models.IntegerField(null=True)
    deputies_source = models.CharField(max_length=10, null=True)
    deputies_year = models.IntegerField(null=True)
    deputies_day_order = models.IntegerField(null=True)
    senate_number = models.IntegerField(null=True)
    senate_source = models.CharField(max_length=10, null=True)
    senate_year = models.IntegerField(null=True)
    senate_day_order = models.IntegerField(null=True)

    origin_chamber = models.CharField(choices=ProjectChambers.choices, max_length=10)
    title = models.TextField()
    # no tiene resumen en principio
    publication_date = models.DateField(null=True)
    status = models.CharField(choices=ProjectStatus.choices, max_length=30, null=True)
    source = models.CharField(max_length=100, null=True)
    text = models.TextField(null=True)
    link = models.CharField(max_length=250, null=True)
    summary = models.TextField(null=True)
    formatted = models.BooleanField(default=False)

    FORMAT_1 = r"\d{1,4}-[A-Z]{1,3}-\d{2}$"  # 70-S-21, 3042-D-21
    FORMAT_2 = r"\d{1,4}-[A-Z]{1,3}-\d{4}$"  # 70-S-2021, 3042-D-2021
    FORMAT_3 = r"0*(\d{4})-[A-Z]{1,3}-\d{4}$"  # 0070-S-2021, 0070-D-2021, 070-S-2021
    FORMAT_4 = r"\d{1,4}-\d{2}$"  # 70-21, 3042-21
    CHAMBER_IDS = ["S", "D", "CD", "PE", "JMG", "OV"]

    FORMAT_1 = r"\d{1,4}-[A-Z]{1,3}-\d{2}$"  # 70-S-21, 3042-D-21
    FORMAT_2 = r"\d{1,4}-[A-Z]{1,3}-\d{4}$"  # 70-S-2021, 3042-D-2021
    FORMAT_3 = r"0*(\d{4})-[A-Z]{1,3}-\d{4}$"  # 0070-S-2021, 0070-D-2021, 070-S-2021
    FORMAT_4 = r"\d{1,4}-\d{2}$"  # 70-21, 3042-21
    CHAMBER_IDS = ["S", "D", "CD", "PE", "JMG", "OV"]

    class Meta:
        unique_together = ("deputies_project_id", "senate_project_id")

    @property
    def project_id(self):
        return self.deputies_project_id or self.senate_project_id

    def get_year(self):
        year = self.deputies_year or self.senate_year
        if year is None:
            return None
        if year < 1000 and year > 75:
            return year + 1900
        elif year < 1000 and year <= 75:
            return year + 2000
        return year

    @classmethod
    def get_project_year_and_number(cls, project_id: str):
        project_id = project_id.replace("/", "-")
        splitted_id = project_id.split("-")
        number = int(splitted_id[0])
        year = int(splitted_id[-1])
        if year > 100:
            # ya tiene formato 19XX o 20XX
            year = year
        elif year > 30:
            # Tiene que ser 19XX
            year += 1900
        else:
            # Tiene que ser 20XX
            year += 2000
        return number, year

    @property
    def authors(self):
        from recoleccion.models import Person

        return Person.objects.filter(authorships__project=self)

    @classmethod
    def get_project_origin_chamber(cls, project_id: str):
        splitted_id = project_id.split("-")
        if len(splitted_id) != 3:
            # Lo más probable es que no se conozca (70-21)
            return None
        raw_chamber = splitted_id[1]

        CHAMBER_MAPPING = {
            "S": ProjectChambers.SENATORS,
            "D": ProjectChambers.DEPUTIES,
            "CD": ProjectChambers.DEPUTIES,
        }
        return CHAMBER_MAPPING.get(raw_chamber, None)

    def __repr__(self):
        return f"LawProject(deputy_project_id: {self.deputies_project_id}, senate_project_id: {self.senate_project_id})"

    def get_summary(self):
        if self.summary:
            return self.summary
        if not self.text:
            raise EmptyText(self.id)
        project_summary = TextSummarizer.summarize_text(self.text)
        self.summary = project_summary
        self.save()
        return project_summary

    @classmethod
    def format_year(cls, year: int | str):
        year = int(year)
        if year < 50:
            return year + 2000
        if year < 100:
            return year + 1900

        return year

    @classmethod
    def split_id(cls, project_id: str):
        if project_id is None:
            return None, None, None
        comps = project_id.split("-")
        if len(comps) == 2:
            num, year = comps
            source = None
        elif len(comps) == 3:
            num, source, year = comps
        else:
            # self.logger.info(f"Invalid project id: {project_id}")
            return None, None, None
        num = int(num)
        source = source.upper() if source else None
        year = cls.format_year(year)
        return num, source, year

    def get_origin_chamber(self):
        """
        Devuelve Diputados o Senado (None si el proyecto no tiene ningún expediente)
        Si el proyecto inició fuera del Congreso (PE), devuelve la cámara por la que ingresó.
        """
        if not self.senate_project_id and not self.deputies_project_id:
            return None
        if not self.senate_project_id:
            return ProjectChambers.DEPUTIES
        elif not self.deputies_project_id:
            return ProjectChambers.SENATORS
        elif self.deputies_source == "S":
            # Si en diputados, la fuente es S, entonces ingresó por el Senado
            return ProjectChambers.SENATORS
        elif self.senate_source in ["D", "CD"]:
            # Si en senado, la fuente es D, entonces ingresó por Diputados
            return ProjectChambers.DEPUTIES
        elif self.senate_source and ("CD" in self.senate_source):
            # Casos borde (tal vez conviene corregirlos) con fuente de Senado CDX.
            # Ejemplo: proyecto con senate_project_id 76-CD5-1988
            return ProjectChambers.DEPUTIES
        else:
            raise ProjectOriginFileConflict(self.pk)

    @property
    def origin_file(self):
        origin_chamber = self.get_origin_chamber()
        if origin_chamber == ProjectChambers.DEPUTIES:
            return self.deputies_project_id
        elif origin_chamber == ProjectChambers.SENATORS:
            return self.senate_project_id
        else:
            return None
