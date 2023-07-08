import pandas as pd

# Project
from vi_library.models.person import Person
from .writer import Writer


class PersonsWriter(Writer):
    model = Person
    
    def get_existing_by_key(self, data):
        if "dni" not in data.columns:
            return {}
        new_dnis = set(data.loc[data["dni"].notnull(), "dni"].unique())
        repeated_persons = Person.query.filter(Person.dni.in_(new_dnis)).all()
        return {person.dni: person for person in repeated_persons}

    def get_key(self, row):
        return row["dni"] if "dni" in row else None

    def create_element(self, row: pd.Series):
        person = Person.objects.create(
            name=row.get("name"),
            last_name=row.get("last_name"),
            dni=row.get("dni"),
            sex=row.get("gender"),
            date_of_birth=row.get("birthdate"),
        )
        return person
