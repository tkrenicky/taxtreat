from __future__ import annotations

import re

ARTICLE_RE = re.compile(
    r"Article\s+(10|11|12)\b(.*?)(?=Article\s+(10|11|12)\b|\Z)",
    re.IGNORECASE | re.DOTALL,
)

PERCENT_RE = re.compile(r"(\d{1,2})\s*%")
OWNERSHIP_RE = re.compile(r"(\d{1,3})\s*(?:per\s*cent|%)", re.IGNORECASE)
BENEFICIAL_OWNER_RE = re.compile(r"beneficial owner", re.IGNORECASE)


def extract_treaty(text: str) -> dict[int, dict]:
    result = {}

    for match in ARTICLE_RE.finditer(text):
        article = int(match.group(1))
        body = match.group(2)

        rates = sorted(
            {int(x) for x in PERCENT_RE.findall(body) if 0 <= int(x) <= 35}
        )

        ownership = None

        match = re.search(
            r"(?:holds?|holding|owned?|ownership).*?(\d{1,3})\s*(?:per\s*cent|%)",
            body,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            ownership = int(match.group(1))

        result[article] = {
            "article": article,
            "rates": rates,
            "beneficial_owner_required": bool(
                BENEFICIAL_OWNER_RE.search(body)
            ),
            "minimum_ownership_percent": ownership,
            "text": body.strip(),
        }

    return result
