from __future__ import annotations

import re
import unicodedata


def _normalize(value: str) -> str:
    value = value.translate(str.maketrans({"õ": "i", "Õ": "I"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.casefold()


RATE_RE = re.compile(r"(\d+)\s*(?:%|procent)", re.IGNORECASE)
OWNERSHIP_RE = re.compile(
    r"nejmene\s+(\d+)\s*(?:%|procent)\s+(?:zakladniho\s+)?kapit",
    re.IGNORECASE,
)
BENEFICIAL_RE = re.compile(
    r"(?:skutecn\w*|opravnen\w*)\s+vlastn",
    re.IGNORECASE,
)


def extract_dividend_rules(text: str) -> dict:
    normalized = _normalize(text)
    rates = sorted({int(rate) for rate in RATE_RE.findall(normalized)})
    ownership = OWNERSHIP_RE.search(normalized)

    return {
        "rates": rates,
        "minimum_ownership_percent": (
            int(ownership.group(1)) if ownership else None
        ),
        "beneficial_owner_required": bool(BENEFICIAL_RE.search(normalized)),
    }
