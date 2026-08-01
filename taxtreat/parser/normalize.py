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

    def replace_article(match: re.Match) -> str:
        number = re.sub(r"\s+", "", match.group(1))
        return f"Článek {number}"

    text = re.sub(
        r"Č\s*l\s*á\s*n\s*e\s*k\s*((?:\d\s*)+)",
        replace_article,
        text,
        flags=re.IGNORECASE,
    )

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



def normalize_detection_page(text: str) -> str:
    """Normalize a page for structural detection without dropping headers.

    PDF extractors sometimes merge a collection header and the treaty title on
    one line. Header removal is useful for legal text parsing, but must not erase
    the only occurrence of ``SMLOUVA`` or ``Článek 1`` used to identify a
    treaty segment.
    """

    lines = [normalize_line(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_detection_pages(pages):
    return [normalize_detection_page(page) for page in pages]

def normalize_pages(pages):
    return [normalize_page(page) for page in pages]
