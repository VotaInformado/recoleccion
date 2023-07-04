from vi_library.models import SenateSeat
from recoleccion.components.writers import LegislatorsWriter
from sqlalchemy import tuple_


class SenatorsWriter(LegislatorsWriter):
    def get_existing_by_key(self, data):
        unique_senators_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()

        seats_info = set(unique_senators_seats.itertuples(index=False, name=None))
        repeated_senators = SenateSeat.query.filter(
            tuple_(SenateSeat.person_id, SenateSeat.start_of_term, SenateSeat.end_of_term).in_(seats_info)
        ).all()
        return {
            (senator.person_id, senator.start_of_term, senator.end_of_term): senator for senator in repeated_senators
        }

    def create_element(self, row):
        senator_seat = SenateSeat(
            person_id=int(row.get("person_id")),
            province=row.get("province"),
            party=row.get("party"),
            start_of_term=row.get("start_of_term"),
            end_of_term=row.get("end_of_term"),
        )
        return senator_seat
