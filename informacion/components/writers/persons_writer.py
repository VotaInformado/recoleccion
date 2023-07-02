from vi_library.models.person import Person
from informacion.components.writers import Writer


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

    def create_element(self, row):
        person = Person.objects.create(
            name=row.get("name", None),
            last_name=row.get("last_name", None),
            dni=row.get("dni", None),
            gender=row.get("gender", None),
            birthdate=row.get("birthdate", None),
        )
        return person
