import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q

# Project
from recoleccion.models.person import Person

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    # Corrects the legislator l

    def handle(self, *args, **options):
        """
        This command was added to the corresponding migration (0048)
        But since then we have added new parties from legislators seats, so we give the possibility to be run again
        """
        legislators = Person.objects.filter(Q(last_party__isnull=True) | Q(last_seat__isnull=True))
        logger.info(f"{len(legislators)} legislators without last party or last seat found")
        total_updated = 0
        for legislator in tqdm(legislators):
            updated = legislator.update_last_party_and_seat()
            if updated:
                total_updated += 1
        logger.info(f"{total_updated} legislators updated")
