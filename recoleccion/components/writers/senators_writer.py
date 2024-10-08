from django.db.models import Q
import pandas as pd
import numpy as np

# Project
from recoleccion.components.utils import date_to_str
from recoleccion.models import SenateSeat, Person
from .legislators_writer import LegislatorsWriter
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class SenatorsWriter(LegislatorsWriter):
    model = SenateSeat
    seat_type = LegislatorSeats.SENATOR

    @classmethod
    def get_existing_by_key(self, data):
        unique_senators_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()
        senators_info = [tuple(row) for row in unique_senators_seats.values]
        repeated_senators = SenateSeat.objects.extra(
            where=["(recoleccion_senateseat.person_id,start_of_term,end_of_term) in %s"],
            params=[tuple(senators_info)],
        )
        return {
            (senator.person_id, date_to_str(senator.start_of_term), date_to_str(senator.end_of_term)): senator
            for senator in repeated_senators
        }

    @classmethod
    def create_element(self, row: pd.Series):
        row = row.replace({pd.NA: None, np.nan: None})
        row = row.rename(index={"party": "party_name"})
        field_names = [field.name for field in SenateSeat._meta.get_fields()] + ["person_id"]
        fields_to_drop = row.index.difference(field_names)
        row = row.drop(fields_to_drop)
        senator_seat = SenateSeat.objects.create(**row)
        return senator_seat

    @classmethod
    def update_element(self, row: pd.Series):
        row.pop("name")
        row.pop("last_name")
        row = row.rename(index={"party": "party_name"})
        row = row.replace({pd.NA: None, np.nan: None})
        return SenateSeat.update_or_raise(**row)
