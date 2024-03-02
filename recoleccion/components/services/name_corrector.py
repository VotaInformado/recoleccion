import ast
import requests
from django.conf import settings
import logging

# Project
from recoleccion.exceptions.custom import NameCorrectorException

logger = logging.getLogger(__name__)


class NameCorrector:
    MAX_TOKENS = 2048
    SYSTEM_CONTEXT = """
    Sos un experto en corregir formato de nombres en español.
    Esto implica principalmente corregir los tildes de los nombres.
    Te voy a enviar un diccionario con nombres y apellidos, y deberás corregir los tildes, si es que necesitan corrección.
    Los nombres son de personas argentinas, por lo que debés corregir los tildes de acuerdo a las reglas del español de Argentina.
    Deberás devolver únicamente el diccionario con los nombres y apellidos corregidos, si es que necesitan corrección.
    De ninguna manera podés agregar información o aclaraciones a la respuesta que no sea el nombre y el apellido corregidos.
    """
    BASE_HEADERS = {
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "messages-2023-12-15",
        "x-api-key": settings.SUMMARIZER_API_KEY,
        "Content-Type": "application/json",
    }
    BASE_MODEL = "claude-2.1"

    @classmethod
    def correct_legislator_name(cls, legislator_info: dict):
        payload = {
            "model": cls.BASE_MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "system": cls.SYSTEM_CONTEXT,
            "messages": [
                {"role": "user", "content": f"Nombres y apellidos: {legislator_info}"},
                {"role": "assistant", "content": "Nombres y apellidos corregidos:"},
            ],
        }
        response = requests.post(settings.SUMMARIZER_URL, headers=cls.BASE_HEADERS, json=payload)
        try:
            raw_info = response.json()["content"][0]["text"]
            corrected_legislator_info: dict = ast.literal_eval(raw_info)
            return corrected_legislator_info
        except Exception as e:
            raise NameCorrectorException(e)
