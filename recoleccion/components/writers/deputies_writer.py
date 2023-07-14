from datetime import datetime as dt

# Project
from vi_library.models.deputy_seat import DeputySeat
from .legislators_writer import LegislatorsWriter


class DeputiesWriter(LegislatorsWriter):
    def get_existing_by_key(self, data):
        unique_deputies_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()
        seats_info = set(unique_deputies_seats.itertuples(index=False, name=None))
        # need to cast uuid to str to compare
        seats_info = tuple([tuple([str(seat[0]), seat[1], seat[2]]) for seat in seats_info])
        repeated_deputies = DeputySeat.objects.extra(
            where=["(recoleccion_deputyseat.person_id::text,start_of_term,end_of_term) in %s"], params=[tuple(seats_info)]
        )
        return {
            (deputy.person_id, deputy.start_of_term, deputy.end_of_term): deputy for deputy in repeated_deputies
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
