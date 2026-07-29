import re
import unicodedata

REPLACEMENTS = {
    "CÏ laÂ nek": "Článek",
    "CÏlaÂnek": "Článek",

    "CÏ eskeÂ": "České",
    "CÏeskeÂ": "České",
    "CÏ eskaÂ": "Česká",
    "CÏeskaÂ": "Česká",

    "SÏvyÂcars": "Švýcars",
    "VsÏ": "Vš",
    "PrÏ": "Př",
    "RÏ": "Ř",
    "SÏ": "Š",
    "ZÏ": "Ž",
    "CÏ": "Č",
    "aÂ": "á",
    "eÂ": "é",
    "iÂ": "í",
    "oÂ": "ó",
    "uÂ": "ú",
    "yÂ": "ý",

    "Ê": "",
    "Â": "",
    "Ï": "",
}


def repair(text: str) -> str:
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def normalize_line(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    line = repair(line)
    line = line.replace("\xa0", " ")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()

def remove_headers(lines):
    cleaned = []

    patterns = [
        r"^Strana\s+\d+",
        r"^\d+$",
        r"^SBI",
        r"^Sb",
        r"^Částka",
    ]

    for line in lines:
        if any(re.search(p, line, re.IGNORECASE) for p in patterns):
            continue
        cleaned.append(line)

    return cleaned


def normalize_page(text):
    lines = [normalize_line(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    lines = remove_headers(lines)
    return "\n".join(lines)


def normalize_pages(pages):
    return [normalize_page(page) for page in pages]
