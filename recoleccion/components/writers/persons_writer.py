import pandas as pd
import numpy as np
import logging

# Project
from recoleccion.models import Person, SocialData
from .writer import Writer

logger = logging.getLogger(__name__)


class PersonsWriter(Writer):
    model = Person

    @classmethod
    def get_missing_persons(cls, data: pd.DataFrame):
        missing_persons = data[data["person_id"].isnull()]
        # Aca pueden quedar personas duplicadas entre sí, pero escritas distintas
        # Se puede usar Dedupe.
        missing_persons = missing_persons.drop_duplicates(subset=["name", "last_name"], keep="last")
        logger.info(f"{len(missing_persons)} new persons will be written to the database")
        return missing_persons

    @classmethod
    def get_existing_persons(cls, data: pd.DataFrame):
        existing_persons = data[data["person_id"].notnull()]
        existing_persons = existing_persons.drop_duplicates(subset=["person_id"], keep="last")
        logger.info(f"{len(existing_persons)} persons will be updated in the database")
        return existing_persons

    @classmethod
    def update_active_persons(cls, modified_persons: list, seat_type: str):
        deactivated_persons = 0
        for person in Person.objects.filter(is_active=True, last_seat=seat_type):
            if person not in modified_persons:
                person.is_active = False
                person.save()
                deactivated_persons += 1
        logger.info(f"{deactivated_persons} persons were deactivated")

    @classmethod
    def write(cls, data: pd.DataFrame, add_social_data=False, update_active_persons=False):
        logger.info(f"Received {len(data)} persons to write")
        modified_persons = []
        missing_persons = cls.get_missing_persons(data)
        existing_persons = cls.get_existing_persons(data)
        for _, row in missing_persons.iterrows():
            person = cls.create_element(row, update_active_persons)
            modified_persons.append(person)
            if add_social_data:
                cls.create_social_data(row, person)
        for _, row in existing_persons.iterrows():
            person = cls.update_element(row, update_active_persons)
            modified_persons.append(person)
        seat_type = data.iloc[0]["seat_type"]
        if update_active_persons:
            cls.update_active_persons(modified_persons, seat_type)
        return modified_persons

    @classmethod
    def get_existing_by_key(self, data):
        if "dni" not in data.columns:
            return {}
        new_dnis = set(data.loc[data["dni"].notnull(), "dni"].unique())
        repeated_persons = Person.query.filter(Person.dni.in_(new_dnis)).all()
        return {person.dni: person for person in repeated_persons}

    @classmethod
    def get_key(self, row):
        return row["dni"] if "dni" in row else None

    @classmethod
    def create_social_data(self, row: pd.Series, person: Person):
        SOCIAL_DATA_FIELDS = ("twitter", "facebook", "instagram", "youtube", "email", "phone", "tiktok")
        social_data = {key: value for key, value in row.items() if key in SOCIAL_DATA_FIELDS}
        social_data["person"] = person
        SocialData.objects.create(**social_data)

    @classmethod
    def create_element(self, row: pd.Series, update_active: bool):
        row = row.replace({pd.NA: None, np.nan: None})
        info = {
            "name": row.get("name"),
            "last_name": row.get("last_name"),
            "dni": row.get("dni", None),
            "sex": row.get("gender", None),
            "date_of_birth": row.get("birthdate", None),
            "last_seat": row.get("seat_type", None),
        }
        if update_active:
            is_active = row.get("is_active", None)
            if is_active is not None:
                info["is_active"] = is_active
            info["last_seat"] = row["seat_type"]
        return Person.objects.create(**info)

    @classmethod
    def update_element(self, row: pd.Series, update_active: bool):
        row = row.replace({pd.NA: None, np.nan: None})
        info = {
            "id": row.get("person_id"),
            "name": row.get("name"),
            "last_name": row.get("last_name"),
            "dni": row.get("dni", None),
            "sex": row.get("gender", None),
            "date_of_birth": row.get("birthdate", None),
        }
        if update_active:
            is_active = row.get("is_active", None)
            if is_active is not None:
                info["is_active"] = is_active
            info["last_seat"] = row["seat_type"]
        return Person.update_or_raise(**info)

    @classmethod
    def update_social_data(cls, data: pd.DataFrame):
        data = data.reset_index(drop=True)
        data = data.replace({pd.NA: None, np.nan: None})
        data = data.drop(columns="full_name")
        data = data.rename(columns={"name": "person_name", "last_name": "person_last_name"})
        created_associated = created_disassociated = updated = 0
        for _, row in data.iterrows():
            row_data = row.to_dict()
            row_data.pop("index")
            if not row_data["person_id"]:
                SocialData.objects.create(**row_data)
                created_disassociated += 1
            else:
                social_data = SocialData.objects.filter(person_id=row_data["person_id"]).first()
                if social_data:
                    social_data.update(**row_data)
                    updated += 1
                else:
                    SocialData.objects.create(**row_data)
                    created_associated += 1
        logger.info(f"{created_associated} social data rows were created associated to a person")
        logger.info(f"{created_disassociated} social data rows were created disassociated")
        logger.info(f"{updated} social data rows were updated")
