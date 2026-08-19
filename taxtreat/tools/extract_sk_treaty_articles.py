from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

SOURCE_QUEUE_PATH = SK_DIR / "treaty_source_review_queue.json"
OUTPUT_PATH = SK_DIR / "treaty_article_machine_extraction.json"
SUMMARY_PATH = SK_DIR / "treaty_article_machine_extraction_summary.json"

ARTICLE_HEADING_RE = re.compile(
    r"\b(?:Článok|Článek)\s+(\d{1,2}[A-Za-z]?)\b",
    re.IGNORECASE,
)

EXPECTED = {
    "dividend": {
        "article": "10",
        "titles": ("dividendy", "dividends"),
    },
    "interest": {
        "article": "11",
        "titles": ("úroky", "uroky", "interest"),
    },
    "royalty": {
        "article": "12",
        "titles": (
            "licenčné",
            "licencne",
            "licenční",
            "licencni",
            "autorské",
            "autorske",
            "royalt",
        ),
    },
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _static_source_url(source_url: str) -> str:
    match = re.search(r"/SK/ZZ/(\d{4})/(\d+)/?$", source_url)
    if match is None:
        raise ValueError(f"Unsupported Slov-Lex source URL: {source_url}")
    year, number = match.groups()
    return (
        "https://static.slov-lex.sk/static/SK/ZZ/"
        f"{year}/{number}/vyhlasene_znenie.html"
    )


def _fetch(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TaxTreat legal-source ingestion/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _normalize_text(html: bytes | str) -> str:
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    return " ".join(soup.get_text(" ", strip=True).split())


def _article_blocks(text: str) -> dict[str, str]:
    matches = list(ARTICLE_HEADING_RE.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        article = match.group(1).upper()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        # Keep the first actual heading block. Cross references use "článku/článku",
        # not the heading form "Článok/Článek", but duplicates can still occur in
        # annexes or parallel-language material and are therefore not overwritten.
        blocks.setdefault(article, block)
    return blocks


def _title_matches(income_type: str, block: str) -> bool:
    prefix = block[:220].lower()
    return any(token in prefix for token in EXPECTED[income_type]["titles"])


def _extract_scope(
    *,
    source_scope: dict[str, Any],
    blocks: dict[str, str],
    source_url: str,
    source_sha256: str,
) -> dict[str, Any]:
    income_type = source_scope["income_type"]
    expected_article = EXPECTED[income_type]["article"]
    block = blocks.get(expected_article)

    if block is None:
        return {
            "packet_id": source_scope["packet_id"],
            "source_country": "SK",
            "recipient_country": source_scope["recipient_country"],
            "income_type": income_type,
            "expected_article": expected_article,
            "source_url": source_url,
            "source_sha256": source_sha256,
            "article_text": None,
            "article_text_sha256": None,
            "machine_extraction_status": "expected_article_heading_not_found",
            "title_validation_status": "not_testable",
            "review_ready": False,
            "human_review_status": "not_started",
            "approval_eligible": False,
            "runtime_status": "not_released",
        }

    article_sha256 = hashlib.sha256(block.encode("utf-8")).hexdigest()
    title_ok = _title_matches(income_type, block)

    return {
        "packet_id": source_scope["packet_id"],
        "source_country": "SK",
        "recipient_country": source_scope["recipient_country"],
        "income_type": income_type,
        "expected_article": expected_article,
        "source_url": source_url,
        "source_sha256": source_sha256,
        "article_text": block,
        "article_text_sha256": article_sha256,
        "machine_extraction_status": (
            "article_extracted"
            if title_ok
            else "article_extracted_title_mismatch_requires_resolution"
        ),
        "title_validation_status": (
            "expected_income_title_matched"
            if title_ok
            else "expected_income_title_not_matched"
        ),
        "review_ready": False,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def parse_treaty(
    *,
    source_relationship: dict[str, Any],
    source_scopes: list[dict[str, Any]],
    html: bytes | str,
) -> dict[str, Any]:
    source_url = _static_source_url(
        source_relationship["official_primary_text_url"]
    )
    source_bytes = html.encode("utf-8") if isinstance(html, str) else html
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    text = _normalize_text(html)
    blocks = _article_blocks(text)

    scopes = [
        _extract_scope(
            source_scope=scope,
            blocks=blocks,
            source_url=source_url,
            source_sha256=source_sha256,
        )
        for scope in source_scopes
    ]

    return {
        "recipient_country": source_relationship["recipient_country"],
        "recipient_country_name": source_relationship["recipient_country_name"],
        "treaty_publication": source_relationship["treaty_publication"],
        "source_url": source_url,
        "source_sha256": source_sha256,
        "article_headings_found": sorted(blocks, key=lambda x: (len(x), x)),
        "scopes": scopes,
        "human_review_status": "not_started",
        "runtime_status": "not_released",
    }


def build_extraction(*, fetch: bool = True) -> dict[str, Any]:
    queue = _load(SOURCE_QUEUE_PATH)
    relationships = queue["relationships"]
    scopes = queue["scopes"]

    if queue["relationship_count"] != 75 or queue["scope_count"] != 225:
        raise ValueError("Treaty source queue must cover 75 relationships / 225 scopes.")

    by_country_scopes: dict[str, list[dict[str, Any]]] = {}
    for scope in scopes:
        by_country_scopes.setdefault(scope["recipient_country"], []).append(scope)

    output_relationships: list[dict[str, Any]] = []
    output_scopes: list[dict[str, Any]] = []

    for relationship in relationships:
        country = relationship["recipient_country"]
        country_scopes = by_country_scopes[country]
        if len(country_scopes) != 3:
            raise ValueError(f"{country}: expected three treaty source scopes.")

        primary_url = relationship["official_primary_text_url"]
        if primary_url is None:
            unresolved = {
                "recipient_country": country,
                "recipient_country_name": relationship["recipient_country_name"],
                "treaty_publication": relationship["treaty_publication"],
                "source_url": None,
                "source_sha256": None,
                "machine_extraction_status": "non_standard_primary_source_pending",
                "human_review_status": "not_started",
                "runtime_status": "not_released",
            }
            output_relationships.append(unresolved)
            for source_scope in country_scopes:
                output_scopes.append({
                    "packet_id": source_scope["packet_id"],
                    "source_country": "SK",
                    "recipient_country": country,
                    "income_type": source_scope["income_type"],
                    "machine_extraction_status": "non_standard_primary_source_pending",
                    "review_ready": False,
                    "human_review_status": "not_started",
                    "approval_eligible": False,
                    "runtime_status": "not_released",
                })
            continue

        source_url = _static_source_url(primary_url)
        if not fetch:
            output_relationships.append({
                "recipient_country": country,
                "recipient_country_name": relationship["recipient_country_name"],
                "treaty_publication": relationship["treaty_publication"],
                "source_url": source_url,
                "machine_extraction_status": "not_fetched",
                "human_review_status": "not_started",
                "runtime_status": "not_released",
            })
            for source_scope in country_scopes:
                output_scopes.append({
                    "packet_id": source_scope["packet_id"],
                    "source_country": "SK",
                    "recipient_country": country,
                    "income_type": source_scope["income_type"],
                    "machine_extraction_status": "not_fetched",
                    "review_ready": False,
                    "human_review_status": "not_started",
                    "approval_eligible": False,
                    "runtime_status": "not_released",
                })
            continue

        html = _fetch(source_url)
        parsed = parse_treaty(
            source_relationship=relationship,
            source_scopes=country_scopes,
            html=html,
        )
        parsed["machine_extraction_status"] = "completed"
        output_relationships.append({
            key: value
            for key, value in parsed.items()
            if key != "scopes"
        })
        output_scopes.extend(parsed["scopes"])

    if len(output_relationships) != 75:
        raise ValueError("Expected 75 treaty extraction relationship rows.")
    if len(output_scopes) != 225:
        raise ValueError("Expected 225 treaty extraction scope rows.")
    if any(row["approval_eligible"] for row in output_scopes):
        raise ValueError("Machine treaty extraction cannot be legal approval.")
    if any(row["runtime_status"] != "not_released" for row in output_scopes):
        raise ValueError("Treaty extraction must remain fail-closed.")

    return {
        "schema_version": 1,
        "dataset_release": "sk-treaty-article-machine-extraction-2026-08-19.1",
        "source_country": "SK",
        "relationship_count": 75,
        "scope_count": 225,
        "policy": {
            "official_primary_text_only": True,
            "article_number_requires_title_validation": True,
            "full_article_text_and_hash_preserved": True,
            "machine_extraction_is_not_semantic_legal_approval": True,
            "human_review_starts_only_after_all_machine_evidence_is_ready": True,
            "runtime_release": False,
        },
        "relationships": output_relationships,
        "scopes": output_scopes,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    scopes = payload["scopes"]
    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "relationship_count": payload["relationship_count"],
        "scope_count": payload["scope_count"],
        "article_extracted_scopes": sum(
            row.get("machine_extraction_status") == "article_extracted"
            for row in scopes
        ),
        "title_mismatch_scopes": sum(
            row.get("machine_extraction_status")
            == "article_extracted_title_mismatch_requires_resolution"
            for row in scopes
        ),
        "missing_article_scopes": sum(
            row.get("machine_extraction_status") == "expected_article_heading_not_found"
            for row in scopes
        ),
        "non_standard_source_scopes": sum(
            row.get("machine_extraction_status") == "non_standard_primary_source_pending"
            for row in scopes
        ),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_extraction(fetch=True)
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Treaty scopes:", summary["scope_count"])
    print("Articles extracted:", summary["article_extracted_scopes"])
    print("Title mismatches:", summary["title_mismatch_scopes"])
    print("Missing headings:", summary["missing_article_scopes"])
    print("Non-standard sources:", summary["non_standard_source_scopes"])


if __name__ == "__main__":
    main()
