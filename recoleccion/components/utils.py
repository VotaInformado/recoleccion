import string
from unidecode import unidecode
from pandas import isna

LOWERCASE_ACCENTS = "áéíóúü"
UPPERCASE_ACCENTS = "ÁÉÍÓÚÜ"



def clean_text_formatting(text, capitalize=True):
    if isna(text):
        return text

    transform_map = str.maketrans(string.punctuation," " * len(string.punctuation)) # remove punctuation
    transform_map.update(str.maketrans(string.whitespace, " " * len(string.whitespace))) # replace whitespace with single space
    transform_map.update(str.maketrans(string.ascii_lowercase + "ñ" + LOWERCASE_ACCENTS, string.ascii_uppercase + "Ñ" + UPPERCASE_ACCENTS)) # uppercase
    cleaner_text = text.translate(transform_map).strip()
    cleaner_text = " ".join(cleaner_text.split()) # remove extra spaces
    if capitalize:
        cleaner_text = capitalize_text(cleaner_text)

    return cleaner_text


def capitalize_text(text):
    words = text.split()
    capitalized_words = [word.capitalize() for word in words]
    text = " ".join(capitalized_words)
    return text


def unidecode_text(text):
    if isna(text):
        return text

    return unidecode(text) # WARNING: removes "ñ" and accents