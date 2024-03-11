from typing import List
from dedupe import Gazetteer, console_label
import os
import pandas as pd

# Project
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions
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

    def get_canonical_data(self, alternative_format=False):
        return self.canonical_data

    def get_record_id(self, record):
        """Gets the record id"""
        raise NotImplementedError

    def train(self, messy_data):
        # if len(messy_data) > len(self.canonical_data):
        #     raise LinkingException(
        #         f"There are more messy records ({len(messy_data)}) than canonical record ({len(self.canonical_data)})"
        #     )
        file_dir = f"{self.TRAINING_DIR}/{self.__class__.__name__}.json"
        canonical_data = self.get_canonical_data()

        if os.path.exists(file_dir):
            with open(file_dir, encoding="utf-8-sig") as f:
                self.gazetteer.prepare_training(messy_data, canonical_data, training_file=f)
        else:
            self.gazetteer.prepare_training(messy_data, canonical_data)
            console_label(self.gazetteer)  # Run active learning because no training data exists
        try:
            self.gazetteer.train()
        except ValueError as e:
            if "Sample larger than population" in str(e):
                self.logger.info("Not enough data to train the Gazetteer, skipping linking...")
                raise IncompatibleLinkingDatasets()
            raise e
        self.gazetteer.index(canonical_data)

    def no_real_matches(self, possible_mappings: List[tuple]):
        # If there is at least one match, then one of the tuples has, in its second element, a list with at least one
        return not any([len(x[1]) > 0 for x in possible_mappings])

    def get_or_save_pending_linking_decision(self, canonical_record, messy_record):
        raise NotImplementedError

    def get_linking_key(self, canonical_data_index: int, messy_record: dict):
        raise NotImplementedError

    def reset_index(self, data_as_dict: dict) -> dict:
        df = pd.DataFrame.from_dict(data_as_dict, orient="index")
        df = df.reset_index(drop=False)
        result_dict = df.to_dict(orient="index")
        return result_dict

    def classify(self, messy_data: dict):
        """
        Receives a dict with the messy data
        Uses the Gazetteer to classify the data in certain, dubious and distinct matches.
        For the dubious matches, it checks if there is a linking decision for the pair (messy, canonical)
        If there isn't, it creates a new one (in PENDING state)
        If there is one, and it has a definitive decision, it moves the record to certain or distinct matches
        Otherwise, it leaves it in dubious matches
        Finally, returns 3 lists: certain_matches, dubious_matches, distinct_matches
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
        created_linking_decisions = existent_linking_decisions = previously_used_decisions = 0

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
                    decision, created = pending_decisions[key]
                    self.logger.info(f"Using existing pending linking decision (id {decision.pk}) for key {key}")
                else:
                    decision, created = self.get_or_save_pending_linking_decision(canonical_record, messy_record)
                    self.logger.info(f"Pending linking decision created (id {decision.uuid}) for key {key}")
                    pending_decisions[key] = (decision, created)
                if created:  # If the decision was just created, it will always be in PENDING
                    created_linking_decisions += 1
                    dubious_matches.append((messy_data_index, canonical_data_index, decision.uuid))
                else:
                    existent_linking_decisions += 1
                    if decision.decision == LinkingDecisionOptions.APPROVED:
                        self.logger.info("Using existing approved linking decision to move record into certain matches")
                        certain_matches.append((messy_data_index, canonical_data_index))
                        previously_used_decisions += 1
                    elif decision.decision == LinkingDecisionOptions.DENIED:
                        self.logger.info("Using existing denied linking decision to move record into distinct matches")
                        distinct_matches.append((messy_data_index, canonical_data_index, confidence_score))
                        previously_used_decisions += 1
                    else:
                        self.logger.info("Existing linking decision is pending")
                        dubious_matches.append((messy_data_index, canonical_data_index, decision.uuid))
            elif confidence_score < dubious_lower_limit:
                distinct_matches.append((messy_data_index, canonical_data_index, confidence_score))

        self._save_training(self.gazetteer)
        self.gazetteer.cleanup_training()
        self.logger.info(f"{previously_used_decisions} previously used linking decisions were used")
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
