from recoleccion.models.linking.party_linking import PartyLinking
from recoleccion.utils.enums.linking_decisions import LinkingDecisions


def create_party_linking_decision(
    messy_denomination: str, canonical_denomination: str, decision: str, record_id: int = None
):
    record_id = record_id if decision == LinkingDecisions.APPROVED else None
    PartyLinking.objects.create(
        denomination=messy_denomination,
        compared_against=canonical_denomination,
        decision=decision,
        party_id=record_id,
    )
