from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from taxtreat.parser.article_parser import parse_articles
from taxtreat.parser.detector import extract_treaty
from taxtreat.parser.extractor import extract_pdf_pages
from taxtreat.parser.models import ParsedTreaty
from taxtreat.parser.publication import resolve_treaty_source
from taxtreat.parser.normalize import normalize_pages
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
    """Parse one treaty only after its counterparty identity is validated."""

    source_path = Path(source_path)
    raw_pages = extract_pdf_pages(source_path)
    selected_pages, resolution = resolve_treaty_source(
        raw_pages,
        country=country,
        source_title=source_title,
    )
    pages = normalize_pages(selected_pages)

    identity = validate_treaty_identity(
        expected_country=country,
        source_title=resolution.effective_title,
        text="\n\n".join(selected_pages),
    )
    if not identity.is_valid:
        raise TreatyIdentityError(identity)

    treaty_text, start_page = extract_treaty(pages)
    articles = parse_articles(treaty_text)

    return ParsedTreaty(
        country=country,
        source_title=resolution.effective_title,
        source_path=str(source_path),
        start_page=resolution.start_page + start_page - 1,
        identity_validation=identity.to_dict(),
        source_resolution=resolution.to_dict(),
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
    print("Treaty starts:", parsed.start_page)
    print("Articles:", len(parsed.articles))
    print()

    for article in parsed.articles[:10]:
        print(article.number, "-", article.title)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
