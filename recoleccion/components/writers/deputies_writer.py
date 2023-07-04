from recoleccion.components.writers import LegislatorsWriter
from pandas import DataFrame
from vi_library.models.deputy_seat import DeputySeat
from datetime import datetime as dt



class DeputiesWriter(LegislatorsWriter):
    def get_existing_by_key(self, data):
        unique_senators_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()

        seats_info = set(unique_senators_seats.itertuples(index=False, name=None))
        repeated_senators = DeputySeat.query.filter(
            tuple_(DeputySeat.person_id, DeputySeat.start_of_term, DeputySeat.end_of_term).in_(seats_info)
        ).all()
        return {
            (senator.person_id, senator.start_of_term, senator.end_of_term): senator for senator in repeated_senators
        }

    def create_element(self, row):
        senator_seat = DeputySeat(
            person_id=int(row.get("person_id")),
            deputy_id=row.get("deputy_id"),
            district=row.get("district"),
            party=row.get("party"),
            start_of_term=row.get("start_of_term"),
            end_of_term=row.get("end_of_term"),
        )
        return senator_seat
