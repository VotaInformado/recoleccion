import pandas as pd

# Project
from recoleccion.models import Person, SocialData
from .writer import Writer


class PersonsWriter(Writer):
    model = Person

    def write(self, data: pd.DataFrame, add_social_data=False):
        written = []
        for _, row in data.iterrows():
            person = self.create_element(row)
            written.append(person)
            if add_social_data:
                self.create_social_data(row, person)
        return written

    def get_existing_by_key(self, data):
        if "dni" not in data.columns:
            return {}
        new_dnis = set(data.loc[data["dni"].notnull(), "dni"].unique())
        repeated_persons = Person.query.filter(Person.dni.in_(new_dnis)).all()
        return {person.dni: person for person in repeated_persons}

    def get_key(self, row):
        return row["dni"] if "dni" in row else None

    def create_social_data(self, row: pd.Series, person: Person):
        SOCIAL_DATA_FIELDS = ("twitter", "facebook", "instagram", "youtube", "email", "phone", "tiktok")
        social_data = {key: value for key, value in row.items() if key in SOCIAL_DATA_FIELDS}
        social_data["person"] = person
        SocialData.objects.create(**social_data)

    def create_element(self, row: pd.Series):
        person = Person.objects.create(
            name=row.get("name"),
            last_name=row.get("last_name"),
            dni=row.get("dni"),
            sex=row.get("gender"),
            date_of_birth=row.get("birthdate"),
        )
        return person
