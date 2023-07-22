from dedupe import Gazetteer, console_label
import os
import pandas as pd
from pprint import pp

# Project
from recoleccion.models.person import Person
from recoleccion.exceptions.custom import LinkingException


DUBIOUS_LOWER_LIMIT = 0.1
DUBIOUS_UPPER_LIMIT = 0.7
MIN_ACCEPTABLE_LOWER_LIMIT = 0.05
MIN_ACCEPTABLE_UPPER_LIMIT = 0.6


class Linker:
    TRAINING_DIR = "recoleccion/components/linkers/training"

    def _save_training(self, gazetteer: Gazetteer):
        with open(f"{self.TRAINING_DIR}/{self.__class__.__name__}.json", "w") as f:
            gazetteer.write_training(f)

    def get_canonical_data(self):
        return self.canonical_data

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
        # if len(messy_data) > len(self.canonical_data):
        #     raise LinkingException(
        #         f"There are more messy records ({len(messy_data)}) than canonical record ({len(self.canonical_data)})"
        #     )
        file_dir = f"{self.TRAINING_DIR}/{self.__class__.__name__}.json"
        if os.path.exists(file_dir):
            with open(file_dir) as f:
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
        # el problema de este d_l_l es que si hay un match con 1e-10 por ej, lo va a tomar como válido
        dubious_lower_limit = max_confidence * DUBIOUS_LOWER_LIMIT
        dubious_upper_limit = max_confidence * DUBIOUS_UPPER_LIMIT
        dubious_lower_limit = max(dubious_lower_limit, MIN_ACCEPTABLE_LOWER_LIMIT)
        dubious_upper_limit = max(dubious_upper_limit, MIN_ACCEPTABLE_UPPER_LIMIT)
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
