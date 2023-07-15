from django.db.models import Q
import pandas as pd

# Project
from vi_library.models import SenateSeat, Person
from .legislators_writer import LegislatorsWriter


class SenatorsWriter(LegislatorsWriter):
    model = SenateSeat
    def get_existing_by_key(self, data):
        unique_senators_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()
        seats_info = set(unique_senators_seats.itertuples(index=False, name=None))
        # need to cast uuid to str to compare
        seats_info = tuple([tuple([str(seat[0]), seat[1], seat[2]]) for seat in seats_info])
        repeated_senators = SenateSeat.objects.extra(
            where=["(recoleccion_senateseat.person_id::text,start_of_term,end_of_term) in %s"], params=[tuple(seats_info)]
        )
        return {
            (senator.person_id, senator.start_of_term, senator.end_of_term): senator for senator in repeated_senators
        }

    def create_element(self, row: pd.Series):
        senator_seat = SenateSeat.objects.create(
            person_id=int(row.get("person_id")),
            province=row.get("province"),
            party=row.get("party"),
            start_of_term=row.get("start_of_term"),
            end_of_term=row.get("end_of_term"),
            is_active=row.get("is_active", False),
        )
        return senator_seat

    def update_element(self, row: pd.Series):
        row.pop("name")
        row.pop("last_name")
        return SenateSeat.update_or_raise(**row)