from dedupe import Gazetteer, console_label
import os
import pandas as pd
from project.models import Person
from pprint import pp
from project.utils import unidecode_text
from datetime import date

DUBIOUS_LOWER_LIMIT = 0.1
DUBIOUS_UPPER_LIMIT = 0.7


class Linker:
    def _save_training(self, gazetteer):
        with open(f"./training/{self.__class__.__name__}.json", "w") as f:
            gazetteer.write_training(f)

    def label_pairs(self, pairs, messy_data):
        """
        Recieves:
         - pairs: A list of tuples of the form (messy_data_index, canonical_data_index)
         - messy_data: The messy data
        Asks for user input to label the pairs as referring to the same entity or not.
        Returns a tuple with two lists:
         - The first list contains the pairs that were labeled as the same entity
         - The second list contains the pairs that were labeled as different entities
        """
        match_records = []
        distinct_records = []
        match_records_ids = []
        distinct_records_ids = []
        print(f"There are {len(pairs)} pairs to label: ")
        for pair in pairs:
            messy_data_index, canonical_data_index = pair

            print("Are these the same records?: \n")
            pp(messy_data[messy_data_index], sort_dicts=True, width=35)
            pp(self.canonical_data[canonical_data_index], sort_dicts=True, width=35)

            response = input("yes (y) / no (n): ").lower()
            while response not in ["y", "n"]:
                print("Invalid response")
                response = input("yes (y) / no (n): ").lower()

            record_pair = (messy_data[messy_data_index], self.canonical_data[canonical_data_index])
            if response == "y":
                match_records.append(record_pair)
                match_records_ids.append(pair)
            elif response == "n":
                distinct_records.append(record_pair)
                distinct_records_ids.append(pair)

        self.gazetteer.mark_pairs({"match": match_records, "distinct": distinct_records})

        return match_records_ids, distinct_records_ids

    def train(self, messy_data):
        if os.path.exists(f"training/{self.__class__.__name__}.json"):
            with open(f"training/{self.__class__.__name__}.json") as f:
                self.gazetteer.prepare_training(messy_data, self.canonical_data, training_file=f)
        else:
            self.gazetteer.prepare_training(messy_data, self.canonical_data)
            console_label(self.gazetteer)  # Run active learning because no training data exists

        self.gazetteer.train()
        self.gazetteer.index(self.canonical_data)

    def classify(self, messy_data):
        possible_mappings = self.gazetteer.search(messy_data, n_matches=1)

        max_conf_pair = max(possible_mappings, key=lambda x: self.confidence(x))
        min_conf_pair = min(possible_mappings, key=lambda x: self.confidence(x))
        max_confidence = max_conf_pair[1][0][1]
        dubious_lower_limit = max_confidence * DUBIOUS_LOWER_LIMIT
        dubious_upper_limit = max_confidence * DUBIOUS_UPPER_LIMIT
        certain_matches = []
        dubious_matches = []
        distinct_matches = []

        for messy_data_index, possible_maps in possible_mappings:
            if len(possible_maps) == 0:
                continue  # No matches
            canonical_data_index, confidence_score = possible_maps[0]  # Get the best match
            if confidence_score > dubious_upper_limit:
                certain_matches.append((messy_data_index, canonical_data_index))
            elif dubious_lower_limit < confidence_score < dubious_upper_limit:
                dubious_matches.append((messy_data_index, canonical_data_index))
            elif confidence_score < dubious_lower_limit:
                distinct_matches.append((messy_data_index, canonical_data_index, confidence_score))

        certain, distinct = self.label_pairs(dubious_matches, messy_data)
        self._save_training(self.gazetteer)
        self.gazetteer.cleanup_training()
        certain_matches.extend(certain)
        distinct_matches.extend(distinct)

        return certain_matches, distinct_matches

    def confidence(self, match):
        return match[1][0][1] if len(match[1]) > 0 else -1


class PersonLinker(Linker):
    fields = [
        {"field": "name", "type": "String"},
        {"field": "last_name", "type": "String"},
    ]

    def __init__(self):
        self.gazetteer = Gazetteer(self.fields)
        self.canonical_data = pd.DataFrame(
            map(lambda x: (x.name, x.last_name, x.id), Person.query.all()), columns=["name", "last_name", "id"]
        )
        self.canonical_data[["name", "last_name"]] = self.canonical_data[["name", "last_name"]].applymap(
            lambda x: unidecode_text(x)
        )
        self.canonical_data = self.canonical_data.to_dict(orient="index")

    def link_persons(self, data):

        messy_data = data.copy()
        messy_data[["name", "last_name"]] = messy_data[["name", "last_name"]].applymap(lambda x: unidecode_text(x))
        messy_data = self._date_to_str(messy_data)

        messy_data = messy_data.to_dict(orient="index")
        self.train(messy_data)
        certain, _ = self.classify(messy_data)

        mapping = [None for x in range(data.shape[0])]

        for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
            canonical_data_id = (
                canonical_data_index + 1
            )  # Don't know why it's necessary maybe: `canonical_data[canonical_data_index].id`?
            mapping[messy_data_index] = canonical_data_id

        data["person_id"] = mapping
        return data

    def _date_to_str(self, data):
        # Convert datetime
        for datetime_column in data.select_dtypes(include=["datetime", "datetimetz"]).columns:
            data[datetime_column] = data[datetime_column].dt.strftime("%Y-%m-%d")

        # Convert date
        for date_column in self._date_cols(data):
            data[date_column] = data[date_column].map(lambda x: x.strftime("%Y-%m-%d"))

        return data

    def _date_cols(self, data):
        date_cols = []
        if data.shape[0] == 0:
            return date_cols

        for col, value in data.iloc[0].iteritems():
            if isinstance(value, date):
                date_cols.append(col)
        return date_cols
