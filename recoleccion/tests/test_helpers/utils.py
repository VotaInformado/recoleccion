from recoleccion.models.linking.party_linking import PartyLinkingDecision
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions


def create_party_linking_decision(messy_denomination: str, canonical_denomination: str, decision: str, record_id: int):
    PartyLinkingDecision.objects.create(
        messy_denomination=messy_denomination,
        decision=decision,
        party_id=record_id,
    )
