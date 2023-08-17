from dedupe import Gazetteer, console_label
import os
from uuid import uuid4
import pandas as pd
from pprint import pp

# Project
from recoleccion.models.person import Person
from recoleccion.exceptions.custom import LinkingException
from recoleccion.models import PersonLinking, PersonLinkingDecisions
from recoleccion.utils.custom_logger import CustomLogger


DUBIOUS_LOWER_LIMIT = 0.1
DUBIOUS_UPPER_LIMIT = 0.7
MIN_ACCEPTABLE_LOWER_LIMIT = 0.05
MIN_ACCEPTABLE_UPPER_LIMIT = 0.6


class Linker:
    TRAINING_DIR = "recoleccion/components/linkers/training"
    logger = CustomLogger("Linker")

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["name"] = record["name"]
        new_record["last_name"] = record["last_name"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def clean_training_pairs(self, gazetteer: Gazetteer):
        distinct_records = gazetteer.training_pairs["distinct"]
        match_records = gazetteer.training_pairs["match"]
        clean_distinct_records, clean_match_records = [], []
        for record_1, record_2 in distinct_records:
            clean_record_1 = self.clean_record(record_1)
            clean_record_2 = self.clean_record(record_2)
            clean_distinct_records.append((clean_record_1, clean_record_2))
        for record_1, record_2 in match_records:
            clean_record_1 = self.clean_record(record_1)
            clean_record_2 = self.clean_record(record_2)
            clean_match_records.append((clean_record_1, clean_record_2))
        new_training_pairs = {"distinct": clean_distinct_records, "match": clean_match_records}
        gazetteer.training_pairs = new_training_pairs

    def _save_training(self, gazetteer: Gazetteer):
        if "tests" not in self.TRAINING_DIR:
            import pdb; pdb.set_trace()
        with open(f"{self.TRAINING_DIR}/{self.__class__.__name__}.json", "w") as f:
            self.clean_training_pairs(gazetteer)
            gazetteer.write_training(f)

    def get_canonical_data(self):
        return self.canonical_data

    def get_person_id(self, messy_name, canonical_name):
        # gets person_id from messy_name. If not found, returns 0, if it is found but not approved, returns -1
        person_link = PersonLinking.objects.filter(full_name=messy_name, compared_against=canonical_name).first()
        if not person_link:
            return 0
        return person_link.person.pk  # will return -1 if denied

    def load_linking(self, person_id, messy_name, canonical_name):
        if person_id < 0:
            decision = PersonLinkingDecisions.DENIED
        else:
            decision = PersonLinkingDecisions.APPROVED
        PersonLinking.objects.create(
            person_id=person_id, full_name=messy_name, compared_against=canonical_name, decision=decision
        )

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
        self.logger.info(f"There are {len(pairs)} pairs to label: ")
        for pair in pairs:
            messy_data_index, canonical_data_index = pair
            record_pair = (messy_data[messy_data_index], self.canonical_data[canonical_data_index])
            messy_name = messy_data[messy_data_index]["name"] + " " + messy_data[messy_data_index]["last_name"]
            canonical_name = (
                self.canonical_data[canonical_data_index]["name"]
                + " "
                + self.canonical_data[canonical_data_index]["last_name"]
            )
            person_id = self.get_person_id(messy_name, canonical_name)
            if person_id > 0:  # approved
                self.logger.info(f"Using approved {messy_name} as {canonical_name}")
                match_records.append(record_pair)
                match_records_ids.append(pair)
                continue
            elif person_id < 0:  # denied
                self.logger.info(f"{messy_name} has been denied as {canonical_name}")
                distinct_records.append(record_pair)
                distinct_records_ids.append(pair)
                continue

            print("Are these the same records?: \n")
            pp(messy_data[messy_data_index], sort_dicts=True, width=35)
            pp(self.canonical_data[canonical_data_index], sort_dicts=True, width=35)

            response = input("yes (y) / no (n): ").lower()
            while response not in ["y", "n"]:
                print("Invalid response")
                response = input("yes (y) / no (n): ").lower()

            if response == "y":
                person_id = self.canonical_data[canonical_data_index]["id"]
                self.load_linking(person_id, messy_name, canonical_name)
                match_records.append(record_pair)
                match_records_ids.append(pair)
            elif response == "n":
                self.load_linking(-1, messy_name, canonical_name)
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
        if self.TRAINING_DIR != "recoleccion/components/linkers/training/tests":
            import pdb; pdb.set_trace()
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
        # TODO: ver esto porque se ve que puede llegar a romper accediendo a un indice que no existe
        dubious_lower_limit = max_confidence * DUBIOUS_LOWER_LIMIT
        dubious_upper_limit = max_confidence * DUBIOUS_UPPER_LIMIT
        # el problema de este d_l_l es que si hay un match con 1e-10 por ej, lo va a tomar como válido
        dubious_lower_limit = max(dubious_lower_limit, MIN_ACCEPTABLE_LOWER_LIMIT)
        dubious_upper_limit = max(dubious_upper_limit, MIN_ACCEPTABLE_UPPER_LIMIT)
        certain_matches = []
        dubious_matches = []
        distinct_matches = []

        for messy_data_index, possible_maps in possible_mappings:
            if len(possible_maps) == 0:
                continue  # No matches
            canonical_data_index, confidence_score = possible_maps[0]  # Get the best match
            messy_name, messy_last_name = (
                messy_data[messy_data_index]["name"],
                messy_data[messy_data_index]["last_name"],
            )
            canonical_name, canonical_last_name = (
                self.canonical_data[canonical_data_index]["name"],
                self.canonical_data[canonical_data_index]["last_name"],
            )
            # hay que agregar este primer paso para que deje de preguntar por los que ya son iguales
            if messy_name == canonical_name and messy_last_name == canonical_last_name:
                certain_matches.append((messy_data_index, canonical_data_index))
            elif confidence_score > dubious_upper_limit:
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
