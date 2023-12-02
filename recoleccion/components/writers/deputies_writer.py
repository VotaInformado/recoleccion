from datetime import datetime as dt
import pandas as pd

# Project
from recoleccion.components.utils import date_to_str
from recoleccion.models.deputy_seat import DeputySeat
from .legislators_writer import LegislatorsWriter
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class DeputiesWriter(LegislatorsWriter):
    model = DeputySeat
    seat_type = LegislatorSeats.DEPUTY

    @classmethod
    def get_existing_by_key(self, data):
        unique_deputies_seats = data.loc[
            data["person_id"].notnull() & data["start_of_term"].notnull() & data["end_of_term"].notnull(),
            ["person_id", "start_of_term", "end_of_term"],
        ].drop_duplicates()
        deputies_info = [tuple(row) for row in unique_deputies_seats.values]
        repeated_deputies = DeputySeat.objects.extra(
            where=["(recoleccion_deputyseat.person_id,start_of_term,end_of_term) in %s"],
            params=[tuple(deputies_info)],
        )
        return {
            (deputy.person_id, date_to_str(deputy.start_of_term), date_to_str(deputy.end_of_term)): deputy
            for deputy in repeated_deputies
        }

    @classmethod
    def create_element(self, row: pd.Series):
        row = row.rename(index={"party": "party_name"})
        field_names = [field.name for field in DeputySeat._meta.get_fields()] + ["person_id"]
        fields_to_drop = row.index.difference(field_names)
        row = row.drop(fields_to_drop)
        senator_seat = DeputySeat.objects.create(**row)
        return senator_seat

    @classmethod
    def update_element(self, row: pd.Series):
        row.pop("name")
        row.pop("last_name")
        row = row.rename(index={"party": "party_name"})
        return DeputySeat.update_or_raise(**row)
