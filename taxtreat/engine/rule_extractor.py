from __future__ import annotations

import re


RATE_RE = re.compile(r"(\d+)\s*procent", re.IGNORECASE)
OWNERSHIP_RE = re.compile(
    r"nejm[eé]n[eě]\s+(\d+)\s+procent\s+kapit",
    re.IGNORECASE,
)
BENEFICIAL_RE = re.compile(
    r"skutečn[ýy]\s+vlastn",
    re.IGNORECASE,
)


def extract_dividend_rules(text: str) -> dict:
    rates = sorted(
        {
            int(rate)
            for rate in RATE_RE.findall(text)
        }
    )

    ownership = OWNERSHIP_RE.search(text)

    return {
        "rates": rates,
        "minimum_ownership_percent":
            int(ownership.group(1))
            if ownership
            else None,
        "beneficial_owner_required":
            bool(BENEFICIAL_RE.search(text)),
    }
