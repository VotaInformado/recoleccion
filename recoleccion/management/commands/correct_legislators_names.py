import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from recoleccion.components.services.name_corrector import NameCorrector
from recoleccion.exceptions.custom import NameCorrectorException

# Project
from recoleccion.models.person import Person

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    MAX_CORRECTIONS_PER_RUN = None

    def handle(self, *args, **options):
        text_formatter = NameCorrector()
        legislators = Person.objects.filter(name_corrected=False)
        for legislator in tqdm(legislators):
            legislator_info = {
                "name": legislator.name,
                "last_name": legislator.last_name,
            }
            try:
                corrected_legislator_info: dict = text_formatter.correct_legislator_name(legislator_info)
                corrected_name = corrected_legislator_info["name"]
                corrected_last_name = corrected_legislator_info["last_name"]
                legislator.name = corrected_name
                legislator.last_name = corrected_last_name
                legislator.name_corrected = True
                legislator.save()
            except NameCorrectorException as e:
                logger.error(f"Skipping legislator with id {legislator.id}: {e}")
                continue
