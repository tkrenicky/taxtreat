from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from taxtreat.parser.article_parser import parse_articles
from taxtreat.parser.detector import treaty_ranges
from taxtreat.parser.extractor import extract_pdf_pages
from taxtreat.parser.models import ParsedTreaty
from taxtreat.parser.normalize import normalize_detection_pages, normalize_pages
from taxtreat.validation.document_identity import (
    TreatyIdentityError,
    TreatyIdentityResult,
    publication_reference,
    validate_treaty_identity,
)


def _rejected_publication_result(
    result: TreatyIdentityResult,
) -> TreatyIdentityResult:
    return replace(
        result,
        status="rejected",
        reason="publication_reference_mismatch",
        warnings=tuple(
            dict.fromkeys((*result.warnings, "publication_reference_not_found"))
        ),
    )


def parse_treaty_file(
    source_path: str | Path,
    *,
    country: str,
    source_title: str,
) -> ParsedTreaty:
    """Select and parse the treaty that matches the requested source metadata."""

    source_path = Path(source_path)
    raw_pages = extract_pdf_pages(source_path)
    raw_text = "\n\n".join(raw_pages)

    # Preserve the document-level diagnostic used by the benchmark. It
    # distinguishes unreadable/scanned sources from readable documents whose
    # treaty structure could not yet be detected. It is not sufficient to
    # select a treaty from a publication containing several legal instruments.
    document_identity = validate_treaty_identity(
        expected_country=country,
        source_title=source_title,
        text=raw_text,
    )
    if document_identity.reason == "insufficient_text":
        raise TreatyIdentityError(document_identity)

    detection_pages = normalize_detection_pages(raw_pages)
    normalized_pages = normalize_pages(raw_pages)

    try:
        ranges = treaty_ranges(detection_pages)
    except RuntimeError:
        if not document_identity.is_valid:
            raise TreatyIdentityError(document_identity)
        raise

    valid_candidates: list[tuple[bool, int, str, TreatyIdentityResult]] = []
    rejected_results: list[TreatyIdentityResult] = []
    expected_reference = publication_reference(source_title)

    for start_index, end_index in ranges:
        identity = validate_treaty_identity(
            expected_country=country,
            source_title=source_title,
            text="\n\n".join(raw_pages[start_index:end_index]),
        )

        if identity.is_valid:
            valid_candidates.append(
                (
                    identity.publication_reference_found is True,
                    start_index + 1,
                    "\n".join(normalized_pages[start_index:end_index]),
                    identity,
                )
            )
        else:
            rejected_results.append(identity)

    if not valid_candidates:
        if not document_identity.is_valid:
            raise TreatyIdentityError(document_identity)
        if rejected_results:
            raise TreatyIdentityError(rejected_results[0])
        raise RuntimeError("Treaty start not found.")

    # A collection PDF may contain several treaties. In that case, an explicit
    # publication reference must identify the selected segment; accepting a
    # country match with a different notice number would break traceability.
    if len(ranges) > 1 and expected_reference is not None:
        exact_reference_candidates = [
            candidate for candidate in valid_candidates if candidate[0]
        ]
        if not exact_reference_candidates:
            raise TreatyIdentityError(
                _rejected_publication_result(valid_candidates[0][3])
            )
        valid_candidates = exact_reference_candidates

    _, start_page, treaty_text, identity = min(
        valid_candidates,
        key=lambda candidate: candidate[1],
    )
    articles = parse_articles(treaty_text)

    return ParsedTreaty(
        country=country,
        source_title=source_title,
        source_path=str(source_path),
        start_page=start_page,
        identity_validation=identity.to_dict(),
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
