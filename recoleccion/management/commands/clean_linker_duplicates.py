import json

# Base command
from django.core.management.base import BaseCommand

# Dates
from datetime import datetime as dt, timezone

# Components
from recoleccion.components.data_sources import CurrentDeputies
from recoleccion.components.linkers import PersonLinker
from recoleccion.components.writers.deputies_writer import DeputiesWriter
from recoleccion.models.person import Person
from recoleccion.utils.enums.legislator_seats import LegislatorSeats


class Command(BaseCommand):
    DEPUTIES_CAPACITY = 257

    def remove_duplicates(self):
        json_file_path = "recoleccion/components/linkers/training/PersonLinker.json"
        # Read the JSON file and parse its content
        with open(json_file_path, "r") as file:
            data = json.load(file)

        # Create a set to track unique tuples based on "name" and "last_name"
        unique_tuples = set()

        # Iterate through the list of tuples
        unique_data = {"distinct": [], "match": []}
        for item in data["distinct"] + data["match"]:
            value = item["__value__"]
            # Convert the value to a tuple of (name, last_name) and check for uniqueness
            item_tuple = tuple((x["name"], x["last_name"]) for x in value)
            if item_tuple not in unique_tuples:
                # Add the item to the unique data
                unique_data["distinct" if item in data["distinct"] else "match"].append(item)
                # Mark the item_tuple as seen
                unique_tuples.add(item_tuple)

        # Write the unique data back to the JSON file
        with open(json_file_path, "w") as file:
            json.dump(unique_data, file, indent=4)

    def handle(self, *args, **options):
        self.remove_duplicates()

    # Example usage
    json_file_path = "path_to_your_json_file.json"
    remove_duplicates(json_file_path)
