from pandas import DataFrame

# Project
from recoleccion.components.writers.writer import Writer
from .persons_writer import PersonsWriter


class LegislatorsWriter(Writer):
    @classmethod
    def write(cls, data: DataFrame, update_active_persons=False):
        cls.logger.info(f"Received {len(data)} legislators to write")
        completed_data = cls.add_missing_persons(data, update_active_persons)
        non_duplicated_data = completed_data.drop_duplicates(
            subset=["person_id", "start_of_term", "end_of_term"], keep="last"
        )
        super().write(non_duplicated_data)

    @classmethod
    def add_missing_persons(cls, persons_data: DataFrame, update_active_persons):
        persons_data["seat_type"] = cls.seat_type
        written = PersonsWriter.write(persons_data, update_active_persons=update_active_persons)
        for person in written:
            persons_data.loc[
                (persons_data["name"] == person.name) & (persons_data["last_name"] == person.last_name),
                "person_id",
            ] = person.id
        return persons_data

    @classmethod
    def get_key(cls, row):
        return (
            row["person_id"],
            row["start_of_term"],
            row["end_of_term"],
        )
