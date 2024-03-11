import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand

# Project
from recoleccion.components.services.text_formatter import TextFormatter
from recoleccion.models.law import Law

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    # Corrects the legislator l

    def handle(self, *args, **options):
        laws_without_title = Law.objects.filter(title="")
        logger.info(f"{len(laws_without_title)} laws without title found")
        for law in tqdm(laws_without_title):
            new_title = law.summary
            corrected_title = TextFormatter.format_text(new_title)
            law.title = corrected_title
            law.save()
