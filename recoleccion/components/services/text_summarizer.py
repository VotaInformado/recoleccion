import requests
from django.conf import settings


# Project
from recoleccion.exceptions.custom import TextSummarizerException


class TextSummarizer:
    SUMMARIZER_URL = settings.SUMMARIZER_URL
    MAX_TOKENS = 2048
    SYSTEM_CONTEXT = """
    Sos un experto que resume proyectos de ley en lenguaje coloquial. Hacés resúmenes completos y 
    detallados, haciendo foco en el objetivo y puntos principales de los proyectos.\n
    Las respuestas solo tendrán el resumen sin ninguna frase o información adicional.
    """
    BASE_HEADERS = {
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "messages-2023-12-15",
        "x-api-key": settings.SUMMARIZER_API_KEY,
        "Content-Type": "application/json",
    }
    BASE_MODEL = "claude-2.1"

    @classmethod
    def _format_text(cls, raw_text: str):
        return raw_text

    @classmethod
    def summarize_text(cls, project_text: str):
        formatted_text = cls._format_text(project_text)
        payload = {
            "model": cls.BASE_MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "system": cls.SYSTEM_CONTEXT,
            "messages": [
                {"role": "user", "content": f"Proyecto de ley: {formatted_text}"},
                {"role": "assistant", "content": "Resumen:"},
            ],
        }
        response = requests.post(cls.SUMMARIZER_URL, headers=cls.BASE_HEADERS, json=payload)
        try:
            response_content = response.json()["content"][0]["text"]
            return response_content
        except Exception as e:
            raise TextSummarizerException(e)
