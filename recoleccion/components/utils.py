import string
from unidecode import unidecode
from pandas import isna
from itertools import islice
from datetime import date

LOWERCASE_ACCENTS = "áéíóúü"
UPPERCASE_ACCENTS = "ÁÉÍÓÚÜ"


def date_to_str(date: date):
    return date.strftime("%Y-%m-%d")


def clean_text_formatting(text, capitalize=True):
    if isna(text):
        return text

    transform_map = str.maketrans(
        string.punctuation, " " * len(string.punctuation)
    )  # remove punctuation
    transform_map.update(
        str.maketrans(string.whitespace, " " * len(string.whitespace))
    )  # replace whitespace with single space
    transform_map.update(
        str.maketrans(
            string.ascii_lowercase + "ñ" + LOWERCASE_ACCENTS,
            string.ascii_uppercase + "Ñ" + UPPERCASE_ACCENTS,
        )
    )  # uppercase
    cleaner_text = text.translate(transform_map).strip()
    cleaner_text = " ".join(cleaner_text.split())  # remove extra spaces
    if capitalize:
        cleaner_text = capitalize_text(cleaner_text)

    return cleaner_text


def digitize_text(text):
    # substracts all non digit characters
    if isna(text) or not text:
        return text

    return "".join([char for char in text if char.isdigit()])


def capitalize_text(text):
    words = text.split()
    capitalized_words = [word.capitalize() for word in words]
    text = " ".join(capitalized_words)
    return text


def trim_extra_spaces(text):
    if isna(text) or not text:
        return text

    return " ".join(text.split())


def unidecode_text(text):
    if isna(text):
        return text

    return unidecode(text)  # WARNING: removes "ñ" and accents


def chunk(it, size):
    # Slices the <it> iterator into tuples of size <size>
    # does not pad the last tuple with None values
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def len_gt(text, length):
    # returns True if the text has more than <length> characters
    # without calculating the len of the text and thus avoiding
    # iterating over the whole text
    try:
        text[length]
        return True
    except IndexError:
        return False
