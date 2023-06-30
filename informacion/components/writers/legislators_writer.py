from project.writers.writer import Writer
from project.writers.persons_writer import PersonsWriter
from pandas import DataFrame


class LegislatorsWriter(Writer):
    def write(self, data: DataFrame):
        completed_data = self.add_missing_persons(data)
        non_duplicated_data = completed_data.drop_duplicates(
            subset=["person_id", "start_of_term", "end_of_term"], keep="last"
        )
        return super().write(non_duplicated_data)

    def add_missing_persons(self, data: DataFrame):
        missing_persons = data[data["person_id"].isnull()][["name", "last_name"]]
        # Aca pueden quedar personas duplicadas entre sí, pero escritas distintas
        # Se puede usar Dedupe.
        missing_persons.drop_duplicates(inplace=True, keep="last")
        persons_writer = PersonsWriter()
        written = persons_writer.write(missing_persons)
        for person in written:
            data.loc[
                (data["name"] == person.name) & (data["last_name"] == person.last_name),
                "person_id",
            ] = person.id
        return data

    def get_key(self, row):
        return (
            row["person_id"],
            row["start_of_term"],
            row["end_of_term"],
        )
