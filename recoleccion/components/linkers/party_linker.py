from typing import Tuple
from dedupe import Gazetteer
import pandas as pd
from django.apps import apps
from collections import OrderedDict


# Project
from recoleccion.models.linking import DENIED_INDICATOR
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import unidecode_text
from recoleccion.models import PartyLinkingDecision
from recoleccion.models.party import PartyDenomination
import logging
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


class PartyLinker(Linker):
    fields = [
        {"field": "denomination", "type": "String"},
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gazetteer = Gazetteer(self.fields)
        self.canonical_data = self.get_canonical_data()

    def get_canonical_data(self) -> dict:
        denominations = PartyDenomination.objects.all().order_by("id")
        canonical_data = pd.DataFrame(
            map(lambda x: (x.denomination, x.party.id), denominations),
            columns=["denomination", "party_id"],
        )
        canonical_data[["denomination"]] = canonical_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        canonical_data = canonical_data.to_dict(orient="index")
        return OrderedDict(canonical_data)

    def get_messy_data(self, original_data: pd.DataFrame) -> dict:
        messy_data = original_data.copy()
        messy_data = messy_data.rename(columns={"party_name": "denomination", "id": "record_id"})
        messy_data[["denomination"]] = messy_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def load_exact_matches(self, messy_data: dict) -> Tuple[pd.DataFrame, dict]:
        """
        First we make sure that exact matches are linked together
        Returns:
            - A DF with columns: denomination, record_id, party_id
            - A dict with unmatched data (with the same format of messy_data)
        """
        party_denominations = PartyDenomination.objects.all()
        denominations_info = {pd.denomination.lower(): pd.party_id for pd in party_denominations}
        matched_data, unmatched_data = {}, {}
        md_index = ud_index = 0
        for id, messy_record in messy_data.items():
            messy_denomination = messy_record["denomination"].lower()
            if messy_denomination in denominations_info:
                matched_data[md_index] = messy_record
                matched_data[md_index]["party_id"] = denominations_info[messy_denomination]
                md_index += 1
            else:
                unmatched_data[ud_index] = messy_record
                ud_index += 1
        matched_df = pd.DataFrame.from_dict(matched_data, orient="index")
        return matched_df, unmatched_data

    def link_parties(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Receives a DF with columns: denomination, record_id
        Returns a DF with columns: denomination, record_id, party_id
        """
        self.logger.info(f"Linking {len(data)} parties...")
        data = data.rename(columns={"id": "record_id"})
        try:
            linked_parties = 0
            messy_data: dict = self.get_messy_data(data)
            exactly_matched_data, unmatched_data = self.load_exact_matches(messy_data)
            self.logger.info(f"Exactly matched {exactly_matched_data.shape[0]} parties")
            manually_linked_data, undefined_data = self.apply_manual_linking(unmatched_data)
            self.logger.info(f"Manually decided on {manually_linked_data.shape[0]} parties")
            undefined_df = pd.DataFrame.from_dict(undefined_data, orient="index")
            try:
                self.train(undefined_data)
            except IncompatibleLinkingDatasets as e:
                undefined_df["party_id"] = None
                return self.merge_dataframes(exactly_matched_data, manually_linked_data, undefined_df)

            certain, dubious, _ = self.classify(undefined_data)
            certain_mapping = [None for x in range(undefined_df.shape[0])]
            for messy_data_index, canonical_data_index in certain:
                canonical_data_id = self.canonical_data[canonical_data_index]["party_id"]
                certain_mapping[messy_data_index] = canonical_data_id
                linked_parties += 1
            undefined_df["party_id"] = certain_mapping
            self.logger.info(f"Linked {linked_parties} parties")
            dubious_mapping = [None for x in range(undefined_df.shape[0])]
            for messy_data_index, canonical_data_index, linking_id in dubious:
                dubious_mapping[messy_data_index] = linking_id
            undefined_df["linking_id"] = dubious_mapping
            unlinked_parties = undefined_df["party_id"].isnull().sum()
            self.logger.info(f"{unlinked_parties} parties remain unlinked")

        except ValueError as e:
            if "first dataset is empty" in str(e) or "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                undefined_df["party_id"] = None
                self.logger.info("Linked 0 parties")
            else:
                raise e
        return self.merge_dataframes(exactly_matched_data, manually_linked_data, undefined_df)

    def are_the_same_record(self, record_1, record_2):
        return record_1["denomination"] == record_2["denomination"]

    def save_linking_decision(self, party_id, denomination, canonical_name):
        if party_id < 0:
            decision = LinkingDecisionOptions.DENIED
        else:
            decision = LinkingDecisionOptions.APPROVED
        party_id = party_id if party_id > 0 else None
        # PartyLinking.objects.create(
        #     party_id=party_id, denomination=denomination, compared_against=canonical_name, decision=decision
        # )

    def _save_pending_decisions(self, identical_pairs):
        pass

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["denomination"] = record["denomination"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def get_record_id(self, record: dict):
        return record["party_id"]

    def approved_linking(self, canonical_id: int, messy_denomination: str) -> Tuple[bool, int]:
        party_link = PartyLinkingDecision.objects.filter(
            messy_denomination__iexact=messy_denomination, party_id=canonical_id
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisionOptions.APPROVED:
                return True, party_link.party_id
        return False, None

    def rejected_linking(self, canonical_id: int, messy_denomination: str) -> bool:
        party_link = PartyLinkingDecision.objects.filter(
            messy_denomination__iexact=messy_denomination, party_id=canonical_id
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisionOptions.DENIED:
                return True
        return False

    def apply_manual_linking(self, messy_data: dict) -> Tuple[pd.DataFrame, dict]:
        """
        Applies previously made decisions to the linking process. To be used before actually using the Gazetteer.
        Receives messy_data, and links it using previously saved decisions
        Returns approved_data, rejected_data and undefined_data
        """
        approved_data, rejected_data = [], []
        undefined_data = {}
        ud_index = 0
        canonical_data: dict = self.get_canonical_data()

        for messy_index, messy_record in messy_data.items():
            messy_denomination = messy_record["denomination"]
            decision_found = False
            for canonical_index, canonical_record in canonical_data.items():
                party_id = canonical_record["party_id"]
                is_approved, party_id = self.approved_linking(party_id, messy_denomination)
                if is_approved:
                    messy_record: dict = messy_data[messy_index]
                    messy_record["party_id"] = party_id
                    approved_data.append(messy_record)
                    decision_found = True
                    break
                elif self.rejected_linking(party_id, messy_denomination):
                    messy_record: dict = messy_data[messy_index]
                    messy_record["party_id"] = DENIED_INDICATOR
                    # we have to differentiate between rejected and undefined
                    rejected_data.append(messy_record)
                    decision_found = True
                    break
            if not decision_found:
                messy_record = messy_data[messy_index]
                undefined_data[ud_index] = messy_record
                ud_index += 1
        manually_linked_data: pd.DataFrame = self.assemble_manually_linked_data(approved_data, rejected_data)
        return manually_linked_data, undefined_data

    def _set_record_id(self, party_denomination_id: int, record_linking_id: int):
        party_id = PartyDenomination.objects.get(id=party_denomination_id).party_id
        classes = ["Authorship", "DeputySeat", "SenateSeat", "Vote"]
        for each_class in classes:
            model = apps.get_model("recoleccion", each_class)
            matches = model.objects.filter(linking_id=record_linking_id)
            matches.update(party_id=party_id)
        canonical_name = PartyDenomination.objects.get(
            party_id=party_id
        ).denomination  # OJO: Denomination id != party id

    def save_pending_linking_decision(self, canonical_record: dict, messy_record: dict) -> int:
        party_id = self.get_record_id(canonical_record)
        messy_denomination = messy_record["denomination"]
        decision = PartyLinkingDecision.objects.create(party_id=party_id, messy_denomination=messy_denomination)
        return decision.uuid

    def get_linking_key(self, canonical_data_index: int, messy_record: dict):
        messy_denomination = messy_record["denomination"]
        return (canonical_data_index, messy_denomination)
