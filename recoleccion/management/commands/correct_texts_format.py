import logging

# Base command
from django.core.management.base import BaseCommand

# Django
from django.db import transaction
from recoleccion.components.services.text_formatter import TextFormatter

# Components
from recoleccion.models import Law, LawProject

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    MAX_CORRECTIONS_PER_RUN = None

    def add_arguments(self, parser):
        parser.add_argument("--class-name", type=str, required=True)

    def handle(self, *args, **options):
        text_formatter = TextFormatter()
        class_name = options["class_name"]
        if class_name == "Law":
            objects = Law.objects.filter(formatted=False)
        elif class_name == "LawProject":
            objects = LawProject.objects.filter(formatted=False)
        if self.MAX_CORRECTIONS_PER_RUN:
            objects = objects[: self.MAX_CORRECTIONS_PER_RUN]
        for object in objects:
            object_title = object.title
            if object_title:
                logger.info(f"Correcting title for {class_name} with id {object.id}")
                corrected_title = text_formatter.format_text(object_title)
                object.title = corrected_title
            object_summary = object.summary
            if object_summary:
                logger.info(f"Correcting summary for {class_name} with id {object.id}")
                corrected_summary = text_formatter.format_text(object_summary)
                object.summary = corrected_summary
            object.formatted = True
            object.save()
