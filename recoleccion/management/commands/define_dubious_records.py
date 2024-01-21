# Base command
from django.core.management.base import BaseCommand
import logging
from pprint import pprint

# Project
from recoleccion.models import LinkingDecision, PartyLinkingDecision, PersonLinkingDecision
from recoleccion.utils.enums.linking_decision_options import LinkingDecisionOptions

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def ask_for_user_decision(self, pending_decision: LinkingDecision) -> str:
        logger.info(f"Pending decision: {pending_decision}")
        while True:
            user_response = input("Make your decision: y(yes), n(no), s(skip): ")
            if user_response == "y":
                return LinkingDecisionOptions.APPROVED
            elif user_response == "n":
                return LinkingDecisionOptions.DENIED
            elif user_response == "s":
                return LinkingDecisionOptions.PENDING
            else:
                print("Invalid response. Please try again.")

    def save_accepted_decision(self, pending_decision: LinkingDecision):
        pending_decision.decision = LinkingDecisionOptions.APPROVED
        pending_decision.save()
        updated_records = pending_decision.update_related_records()
        logger.info(f"Updated {updated_records} records")

    def save_rejected_decision(self, pending_decision: LinkingDecision):
        pending_decision.decision = LinkingDecisionOptions.DENIED
        pending_decision.save()
        unlinked_records = pending_decision.unlink_related_records()
        logger.info(f"Unlinked {unlinked_records} records")

    def handle(self, *args, **options):
        pending_party_decisions = PartyLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING).all()
        pending_person_decisions = PersonLinkingDecision.objects.filter(decision=LinkingDecisionOptions.PENDING).all()
        total_decisions = list(pending_party_decisions) + list(pending_person_decisions)
        logger.info(f"Pending decisions: {len(total_decisions)}")
        sorted_decisions = sorted(total_decisions, key=lambda x: x.id)
        for pending_decision in sorted_decisions:
            user_response = self.ask_for_user_decision(pending_decision)
            if user_response == LinkingDecisionOptions.APPROVED:
                self.save_accepted_decision(pending_decision)
            elif user_response == LinkingDecisionOptions.DENIED:
                self.save_rejected_decision(pending_decision)
            else:
                logger.info("Skipping decision...")
