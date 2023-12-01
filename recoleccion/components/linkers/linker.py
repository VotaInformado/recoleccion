from typing import List, Tuple
from dedupe import Gazetteer, console_label
import os
from uuid import uuid4
import pandas as pd
from pprint import pp
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets

# Project
import logging


class Linker:
    DUBIOUS_LOWER_LIMIT = 0.1
    DUBIOUS_UPPER_LIMIT = 0.7
    MIN_ACCEPTABLE_LOWER_LIMIT = 0.05
    MIN_ACCEPTABLE_UPPER_LIMIT = 0.6
    TRAINING_DIR = "recoleccion/components/linkers/training"
    logger = logging.getLogger(__name__)

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
        with open(f"{self.TRAINING_DIR}/{self.__class__.__name__}.json", "w", encoding="utf-8-sig") as f:
            self.clean_training_pairs(gazetteer)
            gazetteer.write_training(f)

    def get_canonical_data(self):
        return self.canonical_data

    def get_record_id(self, record):
        """Gets the record id"""
        raise NotImplementedError

    def save_linking_decision(self, **kwargs):
        raise NotImplementedError

    def _save_undecided_match(self, canonical_id, messy_record):
        raise NotImplementedError

    def user_approved_linking(self, record_pair: Tuple[dict, dict]) -> bool:
        # Returns True if the user approves the linking, False otherwise
        messy_record, canonical_record = record_pair
        print("Are these the same records?: \n")
        pp(messy_record, sort_dicts=True, width=35)
        pp(canonical_record, sort_dicts=True, width=35)
        response = input("yes (y) / no (n): ").lower()
        while response not in ["y", "n"]:
            print("Invalid response")
            response = input("yes (y) / no (n): ").lower()
        return response == "y"

    # def label_pairs(self, pairs, messy_data):
    #     """
    #     Recieves:
    #      - pairs: A list of tuples of the form (messy_data_index, canonical_data_index, linking_decision_id)
    #      - messy_data: The messy data
    #     Asks for user input to label the pairs as referring to the same entity or not.
    #     Returns a tuple with two lists:
    #      - The first list contains the pairs that were labeled as the same entity
    #      - The second list contains the pairs that were labeled as different entities
    #     """
    #     match_records = []
    #     distinct_records = []
    #     match_records_ids = []
    #     distinct_records_ids = []
    #     self.logger.info(f"There are {len(pairs)} pairs to label: ")
    #     for index_pair in pairs:
    #         messy_data_index, canonical_data_index, _ = index_pair
    #         messy_record, canonical_record = messy_data[messy_data_index], self.canonical_data[canonical_data_index]
    #         record_pair = (messy_record, canonical_record)
    #         # linking_approved = self.user_approved_linking(record_pair)

    #         if linking_approved:
    #             record_id = self.get_record_id(canonical_record)
    #             self.save_linking_decision(record_id, messy_record, canonical_record)
    #             match_records.append(record_pair)
    #             match_records_ids.append(index_pair)
    #         else:
    #             self.save_linking_decision(-1, messy_record, canonical_record)
    #             distinct_records.append(record_pair)
    #             distinct_records_ids.append(index_pair)

    #     self.gazetteer.mark_pairs({"match": match_records, "distinct": distinct_records})
    #     return match_records_ids, distinct_records_ids

    def train(self, messy_data):
        # if len(messy_data) > len(self.canonical_data):
        #     raise LinkingException(
        #         f"There are more messy records ({len(messy_data)}) than canonical record ({len(self.canonical_data)})"
        #     )
        file_dir = f"{self.TRAINING_DIR}/{self.__class__.__name__}.json"

        if os.path.exists(file_dir):
            with open(file_dir, encoding="utf-8-sig") as f:
                self.gazetteer.prepare_training(messy_data, self.canonical_data, training_file=f)
        else:
            self.gazetteer.prepare_training(messy_data, self.canonical_data)
            console_label(self.gazetteer)  # Run active learning because no training data exists
        try:
            self.gazetteer.train()
        except ValueError as e:
            if "Sample larger than population" in str(e):
                self.logger.info("Not enough data to train the Gazetteer, skipping linking...")
                raise IncompatibleLinkingDatasets()
            raise e
        self.gazetteer.index(self.canonical_data)

    def no_real_matches(self, possible_mappings: List[tuple]):
        # If there is at least one match, then one of the tuples has, in its second element, a list with at least one
        return not any([len(x[1]) > 0 for x in possible_mappings])

    def save_pending_linking_decision(self, canonical_record, messy_record):
        raise NotImplementedError

    def get_linking_key(self, canonical_data_index: int, messy_record: dict):
        raise NotImplementedError

    def classify(self, messy_data: dict):
        """
        Receives a dict with the messy data
        Returns 3 lists: certain_matches, undefined_matches, distinct_matches
        """
        if not messy_data:
            return [], [], []  # this means no linking, see the usage of this function
        possible_mappings = self.gazetteer.search(messy_data, n_matches=1)
        if self.no_real_matches(possible_mappings):
            return [], [], []  # this means no linking, see the usage of this function
        max_conf_pair = max(possible_mappings, key=lambda x: self.confidence(x))
        min_conf_pair = min(possible_mappings, key=lambda x: self.confidence(x))
        max_confidence = max_conf_pair[1][0][1]
        # TODO: ver esto porque se ve que puede llegar a romper accediendo a un indice que no existe
        dubious_lower_limit = max_confidence * self.DUBIOUS_LOWER_LIMIT
        dubious_upper_limit = max_confidence * self.DUBIOUS_UPPER_LIMIT
        # el problema de este d_l_l es que si hay un match con 1e-10 por ej, lo va a tomar como válido
        dubious_lower_limit = max(dubious_lower_limit, self.MIN_ACCEPTABLE_LOWER_LIMIT)
        dubious_upper_limit = max(dubious_upper_limit, self.MIN_ACCEPTABLE_UPPER_LIMIT)
        certain_matches = []
        dubious_matches = []
        distinct_matches = []
        pending_decisions = {}

        for messy_data_index, possible_maps in possible_mappings:
            if len(possible_maps) == 0:
                continue  # No matches
            canonical_data_index, confidence_score = possible_maps[0]  # Get the best match
            messy_record = messy_data[messy_data_index]
            canonical_record = self.canonical_data[canonical_data_index]
            # hay que agregar este primer paso para que deje de preguntar por los que ya son iguales
            if self.are_the_same_record(messy_record, canonical_record):
                certain_matches.append((messy_data_index, canonical_data_index))
            elif confidence_score > dubious_upper_limit:
                certain_matches.append((messy_data_index, canonical_data_index))
            elif dubious_lower_limit < confidence_score < dubious_upper_limit:
                key = self.get_linking_key(canonical_data_index, messy_record)
                if key in pending_decisions:
                    decision_id = pending_decisions[key]
                else:
                    decision_id = self.save_pending_linking_decision(canonical_record, messy_record)
                pending_decisions[key] = decision_id
                dubious_matches.append((messy_data_index, canonical_data_index, decision_id))
            elif confidence_score < dubious_lower_limit:
                distinct_matches.append((messy_data_index, canonical_data_index, confidence_score))

        # certain, distinct = self.label_pairs(dubious_matches, messy_data)
        # self._save_undefined_matches(dubious_matches, messy_data)
        self._save_training(self.gazetteer)
        self.gazetteer.cleanup_training()
        # certain_matches.extend(certain)
        # distinct_matches.extend(distinct)

        return certain_matches, dubious_matches, distinct_matches

    def confidence(self, match):
        return match[1][0][1] if len(match[1]) > 0 else -1

    def are_the_same_record(self, record_1, record_2):
        raise NotImplementedError

    def assemble_manually_linked_data(self, approved_data: List[dict], rejected_data: List[dict]) -> pd.DataFrame:
        approved_data = pd.DataFrame(approved_data)
        rejected_data = pd.DataFrame(rejected_data)
        return self.merge_dataframes(approved_data, rejected_data)

    def merge_dataframes(self, *dfs: pd.DataFrame) -> pd.DataFrame:
        merged_data = pd.concat(dfs)
        merged_data = merged_data.reset_index(drop=True)
        return merged_data
