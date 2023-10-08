from django.db import models

VOTE_CHOICE_TRANSLATION = {
    "AFIRMATIVO": "POSITIVE",
    "POSITIVO": "POSITIVE",
    "NEGATIVO": "NEGATIVE",
    "ABSTENCION": "ABSTENTION",
    "ABSTENCIÓN": "ABSTENTION",
    "AUSENTE": "ABSENT",
    "PRESIDENTE": "PRESIDENT",
}


class VoteChoices(models.TextChoices):
    # Ongoing status
    ABSENT = "ABSENT", "Ausente"
    ABSTENTION = "ABSTENTION", "Abstención"
    NEGATIVE = "NEGATIVE", "Negativo"
    POSITIVE = "POSITIVE", "Afirmativo"
    PRESIDENT = ("PRESIDENT", "Presidente")
    # Aparentemente "PRESIDENTE" es una opción

    @classmethod
    def get_choice(cls, value: str):
        if not value:
            raise ValueError("Value can not be None")
        value = value.upper()
        if value in VOTE_CHOICE_TRANSLATION:
            return cls(VOTE_CHOICE_TRANSLATION[value])
        raise ValueError(f"Value {value} not found in {cls.__class__.__name__}")
