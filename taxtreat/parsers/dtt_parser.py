from __future__ import annotations

import re
from dataclasses import dataclass

ARTICLE_RE = re.compile(
    r"Article\s+(10|11|12)\b(.*?)(?=Article\s+(10|11|12)\b|\Z)",
    re.IGNORECASE | re.DOTALL,
)

RATE_RE = re.compile(r"(\d{1,2})\s*%")

@dataclass
class TreatyArticle:
    article: int
    text: str
    rates: list[int]


def parse_articles(text: str) -> list[TreatyArticle]:
    result = []

    for match in ARTICLE_RE.finditer(text):
        article = int(match.group(1))
        body = match.group(2).strip()

        rates = sorted(
            {
                int(rate)
                for rate in RATE_RE.findall(body)
                if 0 <= int(rate) <= 35
            }
        )

        result.append(
            TreatyArticle(
                article=article,
                text=body,
                rates=rates,
            )
        )

    return result
