import requests
from django.conf import settings
import logging

# Project
from recoleccion.exceptions.custom import TextSummarizerException

logger = logging.getLogger(__name__)


class TextFormatter:
    MAX_TOKENS = 2048
    SYSTEM_CONTEXT = """
    Sos un experto en corregir formato textos en español.
    Esto implica principalmente corregir las mayúsculas y minúsculas, y los tildes de los textos,
    además de cualquier otro error que encuentres.
    Únicamente deberás devolver el texto corregido, sin comentarios ni palabras adicionales.
    Si no hay nada por corregir, devolvé el mismo texto.
    """
    BASE_HEADERS = {
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "messages-2023-12-15",
        "x-api-key": settings.SUMMARIZER_API_KEY,
        "Content-Type": "application/json",
    }
    BASE_MODEL = "claude-2.1"

    @classmethod
    def format_text(cls, raw_text: str):
        payload = {
            "model": cls.BASE_MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "system": cls.SYSTEM_CONTEXT,
            "messages": [
                {"role": "user", "content": f"Texto: {raw_text}"},
                {"role": "assistant", "content": "Texto corregido:"},
            ],
        }
        response = requests.post(settings.SUMMARIZER_URL, headers=cls.BASE_HEADERS, json=payload)
        try:
            corrected_text = response.json()["content"][0]["text"]
            return corrected_text
        except Exception as e:
            raise TextSummarizerException(e)
