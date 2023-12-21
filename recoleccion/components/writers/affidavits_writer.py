import pandas as pd

# Project
from recoleccion.components.writers.writer import Writer
from recoleccion.models.affidavit_entry import AffidavitEntry
from recoleccion.utils.enums.affidavit import AffidevitType


class AffidavitsWriter(Writer):
    @classmethod
    def write(cls, data: pd.DataFrame):
        data = data.rename(columns={"full_name": "person_full_name"})
        # we rename here and not in the source because 'full_name' is a better name in the linker
        written = updated = 0
        cls.associated_projects = 0
        for i in data.index:
            row = data.loc[i]
            element, was_created = cls.update_or_create_element(row)
            if was_created:
                written += 1
            else:
                updated += 1
        cls.logger.info(f"{written} affidavits were created and {updated} were updated")
        cls.logger.info(f"{cls.associated_projects} affidavits were associated to projects")

    @classmethod
    def _transform_year(cls, base_year: int, affidavit_type: str):
        if affidavit_type == AffidevitType.INITIAL:
            return base_year - 1
        elif affidavit_type == AffidevitType.ANUAL:
            return base_year
        elif affidavit_type == AffidevitType.FINAL:
            return base_year + 1

    @classmethod
    def _clean_affidavit_value(cls, raw_value: str | float):
        raw_value = str(raw_value)
        return raw_value.replace(".", "").replace("-", ".").replace(",", ".")

    @classmethod
    def update_or_create_element(cls, row: pd.Series):
        row = row.dropna()  # Important, because the writer will try to update or create with null values
        row = row.drop(["index"], errors="ignore")
        try:
            row["year"] = cls._transform_year(row["year"], row["affidavit_type"])
            row["value"] = cls._clean_affidavit_value(row["value"])
        except Exception as e:
            import pdb; pdb.set_trace()
            pass
        affidavit, was_created = AffidavitEntry.objects.update_or_create(
            person_full_name=row["person_full_name"],
            year=row["year"],
            defaults={
                **row.to_dict(),
            },
        )
        return affidavit, was_created
