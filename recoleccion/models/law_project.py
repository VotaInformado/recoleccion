import re
from django.db import models

# Base model
from recoleccion.models.base import BaseModel

# Project
from recoleccion.utils.enums.project_chambers import ProjectChambers
from recoleccion.utils.enums.project_status import ProjectStatus


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
        if year is None: return None
        if year < 1000 and year > 75:
            return year + 1900
        elif year < 1000 and year <= 75:
            return year + 2000
        return year

    @classmethod
    def recognize_format(cls, project_id):
        if re.match(cls.FORMAT_3, project_id):  # FORMAT_3 is the most restrictive
            return cls.FORMAT_3
        elif re.match(cls.FORMAT_1, project_id):
            return cls.FORMAT_1
        elif re.match(cls.FORMAT_2, project_id):
            return cls.FORMAT_2
        elif re.match(cls.FORMAT_4, project_id):
            return cls.FORMAT_4
        return None  # raise Exception

    @classmethod
    def get_all_alternative_ids(cls, original_id: str, include_all_chambers=False):
        original_format = cls.recognize_format(original_id)
        if original_format == cls.FORMAT_1:
            return cls._get_alternative_names_format_1(original_id)
        elif original_format == cls.FORMAT_2:
            return cls._get_alternative_names_format_2(original_id)
        elif original_format == cls.FORMAT_3:
            return cls._get_alternative_names_format_3(original_id)
        elif original_format == cls.FORMAT_4:
            return cls._get_alternative_names_format_4(original_id)

    @classmethod
    def _get_alternative_names_format_1(cls, original_id: str):
        # original format is 70-S-21, 3042-D-21
        id, chamber, year = original_id.split("-")
        full_year = f"20{year}"
        format_2 = f"{id}-{chamber}-{full_year}"
        format_3 = f"{id.zfill(4)}-{chamber}-{full_year}"
        format_4 = f"{id}-{year}"
        result = [original_id, format_2, format_3, format_4]
        if chamber == "D":
            extra_format_2 = f"{id}-CD-{full_year}"
            extra_format_3 = f"{id.zfill(4)}-CD-{full_year}"
            result.extend([extra_format_2, extra_format_3])
        elif chamber == "CD":
            extra_format_2 = f"{id}-D-{full_year}"
            extra_format_3 = f"{id.zfill(4)}-D-{full_year}"
            result.extend([extra_format_2, extra_format_3])
        return result

    @classmethod
    def _get_alternative_names_format_2(cls, original_id: str):
        # original format is 70-S-2021, 3042-D-2021
        id, chamber, year = original_id.split("-")
        format_1 = f"{id}-{chamber}-{year[2:]}"
        format_3 = f"{id.zfill(4)}-{chamber}-{year}"
        format_4 = f"{id}-{year[2:]}"
        result = [original_id, format_1, format_3, format_4]
        if chamber == "D":
            extra_format_1 = f"{id}-CD-{year[2:]}"
            extra_format_3 = f"{id.zfill(4)}-CD-{year}"
            result.extend([extra_format_1, extra_format_3])
        elif chamber == "CD":
            extra_format_1 = f"{id}-D-{year[2:]}"
            extra_format_3 = f"{id.zfill(4)}-D-{year}"
            result.extend([extra_format_1, extra_format_3])
        return result

    @classmethod
    def _get_alternative_names_format_3(cls, original_id: str):
        # original format is 0070-S-2021, 0070-D-2021, 070-S-2021
        def extract_non_zero(id):
            match = re.search(r"0*([1-9]\d*)", id)
            if match:
                return match.group(1)
            return id

        id, chamber, year = original_id.split("-")
        non_zero_id = extract_non_zero(id)
        format_1 = f"{non_zero_id}-{chamber}-{year[2:]}"
        format_2 = f"{non_zero_id}-{chamber}-{year}"
        format_4 = f"{non_zero_id}-{year[2:]}"
        result = [original_id, format_1, format_2, format_4]
        if chamber == "D":
            extra_format_1 = f"{non_zero_id}-CD-{year[2:]}"
            extra_format_2 = f"{non_zero_id}-CD-{year}"
            result.extend([extra_format_1, extra_format_2])
        elif chamber == "CD":
            extra_format_1 = f"{non_zero_id}-D-{year[2:]}"
            extra_format_2 = f"{non_zero_id}-D-{year}"
            result.extend([extra_format_1, extra_format_2])
        return result

    @classmethod
    def _get_alternative_names_format_4(cls, original_id: str):
        # original format is 70-21, 3042-21
        id, year = original_id.split("-")
        possible_results = [original_id]
        full_year = f"20{year}"
        for chamber_id in cls.CHAMBER_IDS:
            format_1 = f"{id}-{chamber_id}-{full_year}"
            format_2 = f"{id.zfill(4)}-{chamber_id}-{full_year}"
            format_3 = f"{id}-{chamber_id}-{year}"
            possible_results.extend([format_1, format_2, format_3])
        return possible_results

    @classmethod
    def get_project_year_and_number(cls, project_id: str):
        project_id = project_id.replace("/", "-")
        splitted_id = project_id.split("-")
        number = splitted_id[0]
        year = splitted_id[-1]
        return int(number), int(year)

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
