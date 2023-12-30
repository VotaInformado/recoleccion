"""
    affidavit_type = models.CharField(choices=AffidavitType.choices, max_length=10)
    term_moment = models.CharField(choices=AffidavitTermMoments.choices, max_length=10)
    asset_type = models.CharField(choices=AffidavitAssetType.choices, max_length=10)
"""

from django.db import models


class AffidevitType(models.TextChoices):
    INITIAL = "Inicial", "Inicial"  # Declaration of assets at the beginning of the legislator's public function
    ANUAL = "Anual", "Anual"  # Annual declaration of assets
    FINAL = "Final", "Final"  # Declaration of assets at the end of the legislator's public function

    @classmethod
    def translate_raw_value(cls, raw_value: str):
        TRANSLATION = {
            0: cls.INITIAL,
            1: cls.ANUAL,
            2: cls.FINAL,
        }
        return TRANSLATION.get(raw_value)

# class AffidevitTermMoments(models.TextChoices):
#     INITIAL = "Inicial", "Inicial"
#     CLOSURE = "Cierre", "Cierre"


# class AffidevitAssetType(models.TextChoices):
#     REAL_ESTATE = "Inmueble", "Inmueble"
#     VEHICLE = "Vehículo", "Vehículo"
#     BANK_ACCOUNT = "Cuenta bancaria", "Cuenta bancaria"
#     OTHER = "Otro", "Otro"
