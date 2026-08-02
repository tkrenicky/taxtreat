from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence
import re

from taxtreat.parser.article_parser import parse_articles
from taxtreat.parser.article_selection import (
    ARTICLE_TYPES,
    select_best_article_sequence,
)
from taxtreat.parser.detector import extract_treaty
from taxtreat.parser.extractor import ExtractionAttempt, ExtractionResult, extract_document
from taxtreat.parser.models import ParsedTreaty, TreatyArticle
from taxtreat.parser.normalize import normalize_pages
from taxtreat.parser.official_source import (
    OfficialSourceError,
    fetch_official_document,
)
from taxtreat.parser.publication import select_treaty_pages
from taxtreat.validation.document_identity import (
    TreatyIdentityError,
    normalize_legal_text,
    validate_treaty_identity,
)


def _article_semantic_score(articles: list[TreatyArticle]) -> int:
    return select_best_article_sequence(articles).semantic_score



def _parse_extraction(
    extraction: ExtractionResult,
    *,
    source_path: Path,
    country: str,
    source_title: str,
    official_url: str | None = None,
) -> ParsedTreaty:
    pages = normalize_pages(extraction.pages)

    selection = select_treaty_pages(
        pages,
        expected_country=country,
        source_title=source_title,
    )
    selected_pages = selection.pages
    effective_title = selection.effective_title or source_title

    identity = validate_treaty_identity(
        expected_country=country,
        source_title=effective_title,
        text="\n\n".join(selected_pages),
    )
    if not identity.is_valid:
        raise TreatyIdentityError(identity)

    treaty_text, relative_start_page = extract_treaty(selected_pages)
    parsed_articles = parse_articles(treaty_text)
    article_selection = select_best_article_sequence(parsed_articles)
    articles = article_selection.articles

    absolute_start_page = selection.start_page + relative_start_page - 1
    source_resolution = selection.to_dict()
    source_resolution.update(
        {
            "article_sequence_index": article_selection.sequence_index,
            "article_sequence_count": article_selection.sequence_count,
            "article_semantic_score": article_selection.semantic_score,
        }
    )
    if official_url:
        source_resolution.update(
            {
                "status": "resolved",
                "method": "official_esbirka_html",
                "official_url": official_url,
            }
        )

    return ParsedTreaty(
        country=country,
        source_title=source_title,
        source_path=str(source_path),
        start_page=absolute_start_page,
        identity_validation=identity.to_dict(),
        text_extraction=extraction.to_dict(),
        source_resolution=source_resolution,
        articles=articles,
    )


def _official_extraction(
    source_title: str,
    *,
    expected_country: str,
) -> tuple[ExtractionResult, str]:
    try:
        official = fetch_official_document(
            source_title,
            expected_country=expected_country,
        )
    except TypeError as exc:
        if "unexpected keyword argument" not in str(exc):
            raise
        official = fetch_official_document(source_title)
    text = "\n".join(official.pages)
    normalized = normalize_legal_text(text)
    article_numbers = tuple(
        sorted(
            {
                int(match.group(1))
                for match in re.finditer(r"(?:clanek|article)\s+(\d{1,3})\b", normalized)
            }
        )
    )
    attempt = ExtractionAttempt(
        method="official_esbirka_html",
        score=min(len(text) // 100, 250) + len(article_numbers) * 20,
        total_characters=len(text),
        substantive_pages=sum(len(page.strip()) >= 100 for page in official.pages),
        article_numbers=article_numbers,
    )
    return (
        ExtractionResult(
            pages=official.pages,
            method="official_esbirka_html",
            score=attempt.score,
            attempts=(attempt,),
        ),
        official.url,
    )


def parse_treaty_file(
    source_path: str | Path,
    *,
    country: str,
    source_title: str,
) -> ParsedTreaty:
    """Run local extraction and one deterministic official-source fallback."""

    source_path = Path(source_path)
    local_error: Exception | None = None
    local_parsed: ParsedTreaty | None = None

    try:
        try:
            local_extraction = extract_document(
                source_path,
                expected_country=country,
                source_title=source_title,
            )
        except TypeError as exc:
            if "unexpected keyword argument" not in str(exc):
                raise
            local_extraction = extract_document(source_path)
        local_parsed = _parse_extraction(
            local_extraction,
            source_path=source_path,
            country=country,
            source_title=source_title,
        )
        if _article_semantic_score(local_parsed.articles) == len(ARTICLE_TYPES):
            return local_parsed
    except Exception as exc:
        local_error = exc

    try:
        official_extraction, official_url = _official_extraction(
            source_title,
            expected_country=country,
        )
        official_parsed = _parse_extraction(
            official_extraction,
            source_path=source_path,
            country=country,
            source_title=source_title,
            official_url=official_url,
        )
        if local_parsed is None:
            return official_parsed
        if _article_semantic_score(official_parsed.articles) >= _article_semantic_score(
            local_parsed.articles
        ):
            return official_parsed
    except (OfficialSourceError, TreatyIdentityError, RuntimeError, ValueError, OSError):
        if local_parsed is not None:
            return local_parsed
        if local_error is not None:
            raise local_error
        raise

    if local_parsed is not None:
        return local_parsed
    if local_error is not None:
        raise local_error
    raise RuntimeError("Treaty parsing produced no result")


def write_parsed_treaty(parsed: ParsedTreaty, output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(parsed.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--country", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    parsed = parse_treaty_file(
        args.pdf,
        country=args.country,
        source_title=args.title,
    )
    write_parsed_treaty(parsed, args.output)

    print()
    print("Country:", parsed.country)
    print("Identity:", parsed.identity_validation["status"])
    print("Extraction:", (parsed.text_extraction or {}).get("method"))
    print("Source resolution:", (parsed.source_resolution or {}).get("status"))
    print("Treaty starts:", parsed.start_page)
    print("Articles:", len(parsed.articles))
    print()

    for article in parsed.articles[:10]:
        print(article.number, "-", article.title)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
