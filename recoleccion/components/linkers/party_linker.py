from typing import List
from dedupe import Gazetteer
import pandas as pd
from datetime import date
from pprint import pp

# Project
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

    def get_canonical_data(
        self,
    ):
        canonical_data = pd.DataFrame(
            map(lambda x: (x.denomination, x.party.id), PartyDenomination.objects.all()),
            columns=["denomination", "party_id"],
        )
        canonical_data[["denomination"]] = canonical_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        canonical_data = canonical_data.to_dict(orient="index")
        return canonical_data

    def get_messy_data(self, original_data: pd.DataFrame):
        messy_data = original_data.copy()
        messy_data = messy_data.rename(columns={"party_name": "denomination", "id": "vote_id"})
        messy_data[["denomination"]] = messy_data[["denomination"]].applymap(lambda x: unidecode_text(x))
        messy_data = messy_data.to_dict(orient="index")
        return messy_data

    def link_parties(self, data: pd.DataFrame):
        self.logger.info(f"Linking {len(data)} parties...")
        data = data.rename(columns={"id": "vote_id"})
        try:
            linked_parties = 0
            messy_data: dict = self.get_messy_data(data)
            self.train(messy_data)
            certain, _ = self.classify(messy_data)
            mapping = [None for x in range(data.shape[0])]
            for messy_data_index, canonical_data_index in certain:  # Probably could be done in paralell
                canonical_data_id = self.canonical_data[canonical_data_index]["party_id"]
                mapping[messy_data_index] = canonical_data_id
                linked_parties += 1

            data["party_id"] = mapping
            self.logger.info(f"Linked {linked_parties} parties")
            unlinked_parties = data["party_id"].isnull().sum()
            self.logger.info(f"{unlinked_parties} parties remain unlinked")
        except ValueError as e:
            if "second dataset is empty" in str(e):
                # Shouldn't be an error, just means that there are no matches
                data["party_id"] = None
                self.logger.info("Linked 0 parties")
            else:
                raise e
        return data

    def are_the_same_record(self, record_1, record_2):
        return record_1["denomination"] == record_2["denomination"]

    def load_linking(self, party_id, denomination, canonical_name):
        if party_id < 0:
            decision = LinkingDecisions.DENIED
        else:
            decision = LinkingDecisions.APPROVED
        PartyLinking.objects.create(
            party_id=party_id, denomination=denomination, compared_against=canonical_name, decision=decision
        )

    def get_record_id(self, messy_data, index_pair):
        # gets person_id from messy_name. If not found, returns 0, if it is found but not approved, returns -1
        messy_data_index, canonical_data_index = index_pair
        messy_denomination = messy_data[messy_data_index]["denomination"]
        canonical_denomination = self.canonical_data[canonical_data_index]["denomination"]
        party_link = PartyLinking.objects.filter(
            denomination=messy_denomination, compared_against=canonical_denomination
        ).first()
        if not party_link:
            return 0
        return party_link.party.pk  # will return -1 if denied

    def clean_record(self, record):
        # for any record, returns name, last_name and id (only if it exists)
        new_record = {}
        new_record["denomination"] = record["denomination"]
        if "id" in record:
            new_record["id"] = record["id"]
        return new_record
