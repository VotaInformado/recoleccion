import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

# Project
from recoleccion.models.law import Law

logger = logging.getLogger(__name__)

SEARCH_LAWS_URL = "https://www.argentina.gob.ar/normativa/buscar?jurisdiccion=nacional&tipo_norma=legislaciones&numero={number}&limit=50&offset=1"


class Command(BaseCommand):

    def handle(self, *args, **options):

        laws = Law.objects.filter(link__isnull=True)
        logger.info(f"{len(laws)} laws without link")
        for law in tqdm(laws):
            law.link = SEARCH_LAWS_URL.format(number=law.law_number)
            law.save()
        logger.info(f"{len(laws)} laws updated")
