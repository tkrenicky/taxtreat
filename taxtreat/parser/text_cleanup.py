import re
import unicodedata


def remove_hyphenation(text: str) -> str:
    return re.sub(r"(?<!\n)(?<=\w)-\s*", "", text)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"[\t\r\f\v]+", " ", text).replace("\n", "\n")


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def clean_text(text: str) -> str:
    cleaned = normalize_unicode(text)
    cleaned = remove_hyphenation(cleaned)
    cleaned = normalize_whitespace(cleaned)
    return cleaned
