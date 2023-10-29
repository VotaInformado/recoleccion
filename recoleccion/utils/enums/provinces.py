from django.db import models
from unidecode import unidecode

PROVINCE_TRANSLATION = {
    "CIUDAD AUTONOMA DE BUENOS AIRES": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "CABA": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "C.A.B.A.": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "C A B A ": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "CAPITAL FEDERAL": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "CIUDAD DE BUENOS AIRES": "CIUDAD AUTONOMA DE BUENOS AIRES",
    "BUENOS AIRES": "BUENOS AIRES",
    "CATAMARCA": "CATAMARCA",
    "CHACO": "CHACO",
    "CHUBUT": "CHUBUT",
    "CORDOBA": "CORDOBA",
    "CORRIENTES": "CORRIENTES",
    "ENTRE RIOS": "ENTRE RIOS",
    "FORMOSA": "FORMOSA",
    "JUJUY": "JUJUY",
    "LA PAMPA": "LA PAMPA",
    "LA RIOJA": "LA RIOJA",
    "MENDOZA": "MENDOZA",
    "MISIONES": "MISIONES",
    "TIERRA DEL FUEGO": "TIERRA DEL FUEGO",
    "TIERRA DEL FUEGO, ANTARTIDA E ISLAS DEL ATLANTICO SUR": "TIERRA DEL FUEGO",
    "TIERRA DEL FUEGO ANTARTIDA E ISLAS DEL ATLANTICO SUR": "TIERRA DEL FUEGO",
    "SANTA FE": "SANTA FE",
    "SALTA": "SALTA",
    "SAN JUAN": "SAN JUAN",
    "SAN LUIS": "SAN LUIS",
    "SANTA CRUZ": "SANTA CRUZ",
    "SANTIAGO DEL ESTERO": "SANTIAGO DEL ESTERO",
    "TUCUMAN": "TUCUMAN",
    "RIO NEGRO": "RIO NEGRO",
    "NEUQUEN": "NEUQUEN",
}


class Provinces(models.TextChoices):
    CABA = "CIUDAD AUTONOMA DE BUENOS AIRES", "Ciudad Autónoma de Buenos Aires"
    BUENOS_AIRES = "BUENOS AIRES", "Buenos Aires"
    CATAMARCA = "CATAMARCA", "Catamarca"
    CHACO = "CHACO", "Chaco"
    CHUBUT = "CHUBUT", "Chubut"
    CORDOBA = "CORDOBA", "Córdoba"
    CORRIENTES = "CORRIENTES", "Corrientes"
    ENTRE_RIOS = "ENTRE RIOS", "Entre Ríos"
    FORMOSA = "FORMOSA", "Formosa"
    JUJUY = "JUJUY", "Jujuy"
    LA_PAMPA = "LA PAMPA", "La Pampa"
    LA_RIOJA = "LA RIOJA", "La Rioja"
    MENDOZA = "MENDOZA", "Mendoza"
    MISIONES = "MISIONES", "Misiones"
    TIERRA_DEL_FUEGO = "TIERRA DEL FUEGO", "Tierra del Fuego"
    SANTA_FE = "SANTA FE", "Santa Fe"
    SALTA = "SALTA", "Salta"
    SAN_JUAN = "SAN JUAN", "San Juan"
    SAN_LUIS = "SAN LUIS", "San Luis"
    SANTA_CRUZ = "SANTA CRUZ", "Santa Cruz"
    SANTIAGO_DEL_ESTERO = "SANTIAGO DEL ESTERO", "Santiago del Estero"
    TUCUMAN = "TUCUMAN", "Tucumán"
    RIO_NEGRO = "RIO NEGRO", "Río Negro"
    NEUQUEN = "NEUQUEN", "Neuquén"

    @classmethod
    def get_choice(cls, value: str):
        if not value:
            raise ValueError("Value can not be None")
        value = unidecode(value).upper().strip()
        if value in PROVINCE_TRANSLATION:
            return cls(PROVINCE_TRANSLATION[value])
        raise ValueError(f"Value {value} not found in {cls.__class__.__name__}")
