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

_ARTICLE_HEADING_COMPACT_RE = re.compile(
    r"(?:c(?:i)?l+a+n+e+k|article)0*(?P<number>\d{1,3})",
    re.IGNORECASE,
)


def _ascii_compact(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def canonicalize_article_heading(line: str) -> str | None:
    """Return one canonical article heading or ``None``.

    PDF text layers often split or corrupt the Czech heading ``Článek`` into
    variants such as ``C Ï l aÂ n e k`` or ``CILAANEK``.  Matching the compact
    accent-free form is deterministic while the full-line requirement avoids
    confusing prose such as ``podle článku 1`` with a heading.
    """

    compact = _ascii_compact(line)
    match = _ARTICLE_HEADING_COMPACT_RE.fullmatch(compact)
    if match is None:
        return None

    return f"Článek {int(match.group('number'))}"


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

    heading = canonicalize_article_heading(line)
    if heading is not None:
        return heading

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
