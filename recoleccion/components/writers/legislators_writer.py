from pandas import DataFrame

# Project
from recoleccion.components.writers.writer import Writer
from .persons_writer import PersonsWriter


class LegislatorsWriter(Writer):

    @classmethod
    def update_active_legislators(cls, written_legislators: list):
        deactivated_legislators = 0
        for legislator in cls.model.objects.filter(is_active=True):
            if legislator not in written_legislators:
                legislator.is_active = False
                legislator.save()
                deactivated_legislators += 1
        cls.logger.info(f"{deactivated_legislators} {cls.model.__name__}s were deactivated")

    @classmethod
    def write(cls, data: DataFrame):
        cls.logger.info(f"Received {len(data)} legislators to write")
        completed_data = cls.add_missing_persons(data)
        non_duplicated_data = completed_data.drop_duplicates(
            subset=["person_id", "start_of_term", "end_of_term"], keep="last"
        )
        written_legislators = super().write(non_duplicated_data)
        cls.update_active_legislators(written_legislators)


    @classmethod
    def add_missing_persons(cls, data: DataFrame):
        missing_persons = data[data["person_id"].isnull()][["name", "last_name"]]
        # Aca pueden quedar personas duplicadas entre sí, pero escritas distintas
        # Se puede usar Dedupe.
        cls.logger.info(f"{len(missing_persons)} new persons will be written to the database")
        missing_persons.drop_duplicates(inplace=True, keep="last")
        persons_writer = PersonsWriter()
        written = persons_writer.write(missing_persons)
        for person in written:
            data.loc[
                (data["name"] == person.name) & (data["last_name"] == person.last_name),
                "person_id",
            ] = person.id
        return data

    @classmethod
    def get_key(cls, row):
        return (
            row["person_id"],
            row["start_of_term"],
            row["end_of_term"],
        )
