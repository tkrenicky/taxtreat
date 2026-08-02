from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .models import TreatyArticle


ARTICLE_TYPES = ("dividend", "interest", "royalty")

# Compact, accent-free heading fragments. Classification is deliberately based
# on headings (plus a short bounded fallback), because complete treaty bodies
# routinely cross-reference dividends, interest and royalties.
_TYPE_MARKERS: dict[str, tuple[str, ...]] = {
    "dividend": ("dividend",),
    "interest": (
        "urok",
        "interest",
        "prijmyzpohledav",
        "incomefromdebtclaim",
        "incomefromclaims",
    ),
    "royalty": ("licenc", "royalt"),
}

_GARBLED_HEADING_RE = re.compile(
    r"(?im)^\s*(?:článek|clanek|article)\s+[^\n]{1,8}\s*$"
)


@dataclass(frozen=True)
class ArticleSequenceSelection:
    articles: list[TreatyArticle]
    sequence_index: int
    sequence_count: int
    semantic_articles: dict[str, TreatyArticle]
    semantic_score: int

    @property
    def is_complete(self) -> bool:
        return all(article_type in self.semantic_articles for article_type in ARTICLE_TYPES)


def _compact(value: str) -> str:
    value = value.translate(str.maketrans({"õ": "i", "Õ": "I"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def article_type(article: TreatyArticle | Mapping[str, object]) -> str | None:
    """Classify a treaty income article independently of article numbering."""

    if isinstance(article, TreatyArticle):
        title = article.title
        body = article.text
    else:
        title = str(article.get("title", ""))
        body = str(article.get("text", ""))

    searchable = _compact(title)
    # Historical scans occasionally place the real heading at the beginning of
    # the body or produce a title consisting only of a number/punctuation.
    if not searchable or searchable[:1].isdigit():
        searchable += _compact(body[:240])

    for candidate, markers in _TYPE_MARKERS.items():
        if any(marker in searchable for marker in markers):
            return candidate
    return None


def _embedded_heading(
    text: str,
    current_type: str | None,
) -> tuple[re.Match[str], str, str] | None:
    expected = {
        "dividend": "interest",
        "interest": "royalty",
    }.get(current_type)
    if expected is None:
        return None

    for match in _GARBLED_HEADING_RE.finditer(text):
        remainder = text[match.end():]
        lines = [line.strip() for line in remainder.splitlines() if line.strip()]
        if not lines:
            continue
        title = lines[0]
        if article_type(TreatyArticle(number=0, title=title, text="")) == expected:
            return match, title, expected
    return None


def repair_embedded_article_headings(articles: Sequence[TreatyArticle]) -> list[TreatyArticle]:
    """Recover OCR-damaged numeric headings embedded in the preceding body.

    Typical scans turn ``Článek 11`` into ``Článek al`` or ``Článek it``. The
    recovery remains deterministic: the next visible semantic heading must be
    the category that normally follows the current income article.
    """

    repaired: list[TreatyArticle] = []
    queue = list(articles)

    while queue:
        article = queue.pop(0)
        split = _embedded_heading(article.text, article_type(article))
        if split is None:
            repaired.append(article)
            continue

        match, title, _ = split
        remainder = article.text[match.end():]
        title_position = remainder.find(title)
        if title_position >= 0:
            remainder = remainder[title_position + len(title):]

        repaired.append(
            TreatyArticle(
                number=article.number,
                title=article.title,
                text=article.text[:match.start()].strip(),
                paragraphs=list(article.paragraphs),
            )
        )
        # Put the recovered article back into the queue so a second damaged
        # heading (e.g. Article 12) can be recovered in the same way.
        queue.insert(
            0,
            TreatyArticle(
                number=article.number + 1,
                title=title,
                text=remainder.strip(),
                paragraphs=[],
            ),
        )

    return repaired


def split_article_sequences(articles: Sequence[TreatyArticle]) -> list[list[TreatyArticle]]:
    """Split a multi-act publication whenever article numbering restarts."""

    sequences: list[list[TreatyArticle]] = []
    current: list[TreatyArticle] = []
    previous: int | None = None

    for article in articles:
        if current and previous is not None and article.number <= previous:
            sequences.append(current)
            current = []
        current.append(article)
        previous = article.number

    if current:
        sequences.append(current)
    return sequences


def semantic_articles(articles: Iterable[TreatyArticle]) -> dict[str, TreatyArticle]:
    result: dict[str, TreatyArticle] = {}
    for article in articles:
        candidate = article_type(article)
        if candidate and candidate not in result:
            result[candidate] = article
    return result


def _sequence_score(sequence: Sequence[TreatyArticle]) -> tuple[int, int, int, int, int]:
    classified = semantic_articles(sequence)
    numbers = {article.number for article in sequence}
    continuity = 0
    for number in range(1, 100):
        if number not in numbers:
            break
        continuity += 1
    text_length = sum(len(article.title) + len(article.text) for article in sequence)
    return (
        int(all(name in classified for name in ARTICLE_TYPES)),
        len(classified),
        int(1 in numbers),
        continuity,
        text_length,
    )


def select_best_article_sequence(articles: Sequence[TreatyArticle]) -> ArticleSequenceSelection:
    repaired = repair_embedded_article_headings(articles)
    sequences = split_article_sequences(repaired)
    if not sequences:
        return ArticleSequenceSelection([], 0, 0, {}, 0)

    ranked = [(_sequence_score(sequence), index, sequence) for index, sequence in enumerate(sequences)]
    # ``max`` keeps the first item on an exact tie, which is desirable for
    # Czech/English duplicate versions after publication selection.
    _, index, selected = max(ranked, key=lambda item: item[0])
    classified = semantic_articles(selected)
    return ArticleSequenceSelection(
        articles=list(selected),
        sequence_index=index,
        sequence_count=len(sequences),
        semantic_articles=classified,
        semantic_score=len(classified),
    )


def articles_from_payload(items: Sequence[Mapping[str, object]]) -> list[TreatyArticle]:
    result: list[TreatyArticle] = []
    for item in items:
        raw_number = item.get("number", "")
        try:
            number = int(raw_number)
        except (TypeError, ValueError):
            continue
        result.append(
            TreatyArticle(
                number=number,
                title=str(item.get("title", "")),
                text=str(item.get("text", "")),
                paragraphs=[str(value) for value in item.get("paragraphs", []) or []],
            )
        )
    return result
