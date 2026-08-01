from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from taxtreat.parser.article_parser import parse_articles
from taxtreat.parser.detector import extract_treaty
from taxtreat.parser.extractor import extract_document
from taxtreat.parser.models import ParsedTreaty
from taxtreat.parser.normalize import normalize_pages
from taxtreat.parser.publication import select_treaty_pages
from taxtreat.validation.document_identity import (
    TreatyIdentityError,
    validate_treaty_identity,
)


def parse_treaty_file(
    source_path: str | Path,
    *,
    country: str,
    source_title: str,
) -> ParsedTreaty:
    """Run the generic extraction, source selection and parsing pipeline."""

    source_path = Path(source_path)
    extraction = extract_document(source_path)
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
    articles = parse_articles(treaty_text)

    absolute_start_page = selection.start_page + relative_start_page - 1
    return ParsedTreaty(
        country=country,
        source_title=source_title,
        source_path=str(source_path),
        start_page=absolute_start_page,
        identity_validation=identity.to_dict(),
        text_extraction=extraction.to_dict(),
        source_resolution=selection.to_dict(),
        articles=articles,
    )


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
