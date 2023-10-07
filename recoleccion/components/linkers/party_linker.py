from typing import List, Tuple
from dedupe import Gazetteer
import pandas as pd
from datetime import date
from pprint import pp

# Project
from recoleccion.exceptions.custom import IncompatibleLinkingDatasets
from recoleccion.components.linkers import Linker
from recoleccion.components.utils import unidecode_text
from recoleccion.models import PartyLinking
from recoleccion.models.party import PartyDenomination
from recoleccion.utils.custom_logger import CustomLogger
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


class PartyLinker(Linker):
    fields = [
        {"field": "denomination", "type": "String"},
    ]

    def __init__(self):
        self.logger = CustomLogger(self.__class__.__name__)
        self.gazetteer = Gazetteer(self.fields)
        self.canonical_data = self.get_canonical_data()

    def get_canonical_data(self) -> dict:
        canonical_data = pd.DataFrame(
            map(lambda x: (x.denomination, x.party.id), PartyDenomination.objects.all()),
            columns=["denomination", "party_id"],
        )
        canonical_data[["denomination"]] = canonical_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        canonical_data = canonical_data.to_dict(orient="index")
        return canonical_data

    def get_messy_data(self, original_data: pd.DataFrame) -> dict:
        messy_data = original_data.copy()
        messy_data = messy_data.rename(columns={"party_name": "denomination", "id": "record_id"})
        messy_data[["denomination"]] = messy_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

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
            manually_linked_data, undefined_data = self.apply_manual_linking(messy_data)
            self.logger.info(f"Manually decided on {manually_linked_data.shape[0]} parties")
            undefined_df = pd.DataFrame.from_dict(undefined_data, orient="index")
            try:
                self.train(messy_data)
            except IncompatibleLinkingDatasets as e:
                undefined_df["party_id"] = None
                return self.merge_dataframes(manually_linked_data, undefined_df)

            certain, _ = self.classify(undefined_data)
            mapping = [None for x in range(undefined_df.shape[0])]
            for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
                canonical_data_id = self.canonical_data[canonical_data_index]["party_id"]
                mapping[messy_data_index] = canonical_data_id
                linked_parties += 1

            undefined_df["party_id"] = mapping
            self.logger.info(f"Linked {linked_parties} parties")
            unlinked_parties = undefined_df["party_id"].isnull().sum()
            self.logger.info(f"{unlinked_parties} parties remain unlinked")
        except ValueError as e:
            if "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                undefined_df["party_id"] = None
                self.logger.info("Linked 0 parties")
            else:
                raise e
        return self.merge_dataframes(manually_linked_data, undefined_df)

    def are_the_same_record(self, record_1, record_2):
        return record_1["denomination"] == record_2["denomination"]

    def save_linking_decision(self, party_id, denomination, canonical_name):
        if party_id < 0:
            decision = LinkingDecisions.DENIED
        else:
            decision = LinkingDecisions.APPROVED
        party_id = party_id if party_id > 0 else None
        PartyLinking.objects.create(
            party_id=party_id, denomination=denomination, compared_against=canonical_name, decision=decision
        )

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["denomination"] = record["denomination"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record

    def get_record_id(self, record: dict):
        return record["party_id"]

    def approved_linking(self, canonical_denomination: str, messy_denomination: str) -> Tuple[bool, int]:
        party_link = PartyLinking.objects.filter(
            denomination__iexact=messy_denomination, compared_against__iexact=canonical_denomination
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisions.APPROVED:
                return True, party_link.party_id
        return False, None

    def rejected_linking(self, canonical_denomination: str, messy_denomination: str) -> bool:
        party_link = PartyLinking.objects.filter(
            denomination__iexact=messy_denomination, compared_against__iexact=canonical_denomination
        ).first()
        if party_link:
            if party_link.decision == LinkingDecisions.DENIED:
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
        canonical_data: dict = self.get_canonical_data()

        for messy_index, messy_record in messy_data.items():
            messy_denomination = messy_record["denomination"]
            decision_found = False
            for canonical_index, canonical_record in canonical_data.items():
                canonical_denomination = canonical_record["denomination"]
                is_approved, party_id = self.approved_linking(canonical_denomination, messy_denomination)
                if is_approved:
                    messy_record: dict = messy_data[messy_index]
                    messy_record["party_id"] = party_id
                    approved_data.append(messy_record)
                    decision_found = True
                    break
                elif self.rejected_linking(canonical_denomination, messy_denomination):
                    messy_record: dict = messy_data[messy_index]
                    messy_record["party_id"] = None
                    rejected_data.append(messy_record)
                    decision_found = True
                    break
            if not decision_found:
                messy_record = messy_data[messy_index]
                undefined_data[messy_index] = messy_record
        manually_linked_data: pd.DataFrame = self.assemble_manually_linked_data(approved_data, rejected_data)
        return manually_linked_data, undefined_data
