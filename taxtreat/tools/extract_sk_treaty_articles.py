from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import tempfile
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
    r"\b(?:Článok|Článek|Čl\.)\s+(\d{1,2}[A-Za-z]?)\b",
    re.IGNORECASE,
)

EXPECTED = {
    "dividend": {
        "article": "10",
        "titles": ("dividendy", "dividends"),
    },
    "interest": {
        "article": "11",
        "titles": (
            "úroky",
            "uroky",
            "interest",
            "príjmy z dlhových pohľadávok",
            "prijmy z dlhovych pohladavok",
        ),
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
            "príjmy z autorských práv a licencií",
            "prijmy z autorskych prav a licencii",
        ),
    },
}

# Some official publications expose the treaty body only as a PDF attachment
# or, in Taiwan's case, in the official Ministry of Finance Financial Bulletin.
# These remain primary official sources and encode no legal conclusion.
OFFICIAL_PDF_OVERRIDES = {
    "OM": (
        "https://static.slov-lex.sk/pdf/prilohy/SK/ZZ/2021/548/"
        "vyhlasene_znenie_5381567-2.pdf"
    ),
    "TW": (
        "https://www.mfsr.sk/files/archiv/financny-spravodajca/"
        "3497/63/FS_09_2011.pdf"
    ),
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
            "Accept": "text/html,application/xhtml+xml,application/pdf",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _pdf_to_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = " ".join((page.extract_text() or "") for page in reader.pages)
        if text.strip():
            return " ".join(text.split())
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "source.pdf"
        txt_path = Path(tmp) / "source.txt"
        pdf_path.write_bytes(pdf_bytes)
        completed = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0 or not txt_path.exists():
            raise RuntimeError(
                "Official PDF treaty text could not be extracted with pypdf "
                "or pdftotext."
            )
        return " ".join(txt_path.read_text(encoding="utf-8", errors="replace").split())


def _normalize_text(source: bytes | str, *, content_type: str = "html") -> str:
    if content_type == "pdf":
        if isinstance(source, str):
            source = source.encode("utf-8")
        return _pdf_to_text(source)

    if isinstance(source, bytes):
        source = source.decode("utf-8", errors="replace")
    soup = BeautifulSoup(source, "lxml")
    return " ".join(soup.get_text(" ", strip=True).split())


def _article_blocks(text: str) -> dict[str, str]:
    matches = list(ARTICLE_HEADING_RE.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        article = match.group(1).upper()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        blocks.setdefault(article, block)
    return blocks


def _title_matches(income_type: str, block: str) -> bool:
    prefix = block[:260].lower()
    return any(token in prefix for token in EXPECTED[income_type]["titles"])


def _article_text_is_substantive(block: str) -> bool:
    # A number of Slov-Lex static pages expose only the article heading and
    # paragraph/list markers (e.g. "Článok 10 Dividendy 1. 2. a) b) ...").
    # Such a block is not legal text and must never enter semantic extraction.
    words = re.findall(r"[A-Za-zÀ-ž]{3,}", block)
    return len(block) >= 300 and len(words) >= 30


def _resolve_article(
    *,
    income_type: str,
    blocks: dict[str, str],
) -> tuple[str | None, str | None, str]:
    expected_article = EXPECTED[income_type]["article"]
    expected_block = blocks.get(expected_article)

    if expected_block is not None and _title_matches(income_type, expected_block):
        return expected_article, expected_block, "expected_number_and_title_matched"

    title_matches = [
        (article, block)
        for article, block in blocks.items()
        if _title_matches(income_type, block)
    ]

    if len(title_matches) == 1:
        actual_article, block = title_matches[0]
        return actual_article, block, "resolved_by_unique_income_title"

    if len(title_matches) > 1:
        return None, None, "ambiguous_multiple_income_title_matches"

    if expected_block is None:
        return None, None, "expected_article_heading_not_found"

    return expected_article, expected_block, "expected_number_title_mismatch_unresolved"


def _extract_scope(
    *,
    source_scope: dict[str, Any],
    blocks: dict[str, str],
    source_url: str,
    source_sha256: str,
) -> dict[str, Any]:
    income_type = source_scope["income_type"]
    expected_article = EXPECTED[income_type]["article"]
    actual_article, block, resolution = _resolve_article(
        income_type=income_type,
        blocks=blocks,
    )

    base = {
        "packet_id": source_scope["packet_id"],
        "source_country": "SK",
        "recipient_country": source_scope["recipient_country"],
        "income_type": income_type,
        "expected_article": expected_article,
        "actual_article": actual_article,
        "article_resolution_status": resolution,
        "source_url": source_url,
        "source_sha256": source_sha256,
        "review_ready": False,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }

    if block is None:
        return {
            **base,
            "article_text": None,
            "article_text_sha256": None,
            "machine_extraction_status": "validated_article_not_resolved",
            "title_validation_status": "not_validated",
        }

    title_ok = _title_matches(income_type, block)
    article_sha256 = hashlib.sha256(block.encode("utf-8")).hexdigest()

    if title_ok and not _article_text_is_substantive(block):
        return {
            **base,
            "article_text": block,
            "article_text_sha256": article_sha256,
            "machine_extraction_status": "article_extracted_non_substantive_requires_recovery",
            "title_validation_status": "expected_income_title_matched_but_content_missing",
        }

    if not title_ok:
        return {
            **base,
            "article_text": block,
            "article_text_sha256": article_sha256,
            "machine_extraction_status": "article_extracted_title_mismatch_requires_resolution",
            "title_validation_status": "expected_income_title_not_matched",
        }

    status = (
        "article_extracted"
        if actual_article == expected_article
        else "article_extracted_by_title_number_variance"
    )
    return {
        **base,
        "article_text": block,
        "article_text_sha256": article_sha256,
        "machine_extraction_status": status,
        "title_validation_status": "expected_income_title_matched",
    }


def parse_treaty(
    *,
    source_relationship: dict[str, Any],
    source_scopes: list[dict[str, Any]],
    html: bytes | str,
    source_url_override: str | None = None,
    content_type: str = "html",
) -> dict[str, Any]:
    source_url = source_url_override or _static_source_url(
        source_relationship["official_primary_text_url"]
    )
    source_bytes = html.encode("utf-8") if isinstance(html, str) else html
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    text = _normalize_text(html, content_type=content_type)
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
        "source_content_type": content_type,
        "article_headings_found": sorted(blocks, key=lambda x: (len(x), x)),
        "scopes": scopes,
        "human_review_status": "not_started",
        "runtime_status": "not_released",
    }


def _unresolved_rows(
    relationship: dict[str, Any],
    country_scopes: list[dict[str, Any]],
    status: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    relationship_row = {
        "recipient_country": relationship["recipient_country"],
        "recipient_country_name": relationship["recipient_country_name"],
        "treaty_publication": relationship["treaty_publication"],
        "source_url": None,
        "source_sha256": None,
        "machine_extraction_status": status,
        "human_review_status": "not_started",
        "runtime_status": "not_released",
    }
    scope_rows = [
        {
            "packet_id": scope["packet_id"],
            "source_country": "SK",
            "recipient_country": relationship["recipient_country"],
            "income_type": scope["income_type"],
            "machine_extraction_status": status,
            "review_ready": False,
            "human_review_status": "not_started",
            "approval_eligible": False,
            "runtime_status": "not_released",
        }
        for scope in country_scopes
    ]
    return relationship_row, scope_rows


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
        pdf_override = OFFICIAL_PDF_OVERRIDES.get(country)

        if primary_url is None and pdf_override is None:
            rel_row, scope_rows = _unresolved_rows(
                relationship,
                country_scopes,
                "non_standard_primary_source_pending",
            )
            output_relationships.append(rel_row)
            output_scopes.extend(scope_rows)
            continue

        source_url = pdf_override or _static_source_url(primary_url)
        content_type = "pdf" if pdf_override else "html"

        if not fetch:
            rel_row, scope_rows = _unresolved_rows(
                relationship,
                country_scopes,
                "not_fetched",
            )
            rel_row["source_url"] = source_url
            output_relationships.append(rel_row)
            output_scopes.extend(scope_rows)
            continue

        source = _fetch(source_url)
        parsed = parse_treaty(
            source_relationship=relationship,
            source_scopes=country_scopes,
            html=source,
            source_url_override=source_url,
            content_type=content_type,
        )

        # Slov-Lex's static rendering can contain only headings/list markers.
        # Retry the official public eZbierka page, which exposes the expanded
        # legal text server-side, before declaring the relationship unresolved.
        weak_status = "article_extracted_non_substantive_requires_recovery"
        if (
            pdf_override is None
            and primary_url is not None
            and any(
                row.get("machine_extraction_status") == weak_status
                for row in parsed["scopes"]
            )
        ):
            try:
                public_source = _fetch(primary_url)
                recovered = parse_treaty(
                    source_relationship=relationship,
                    source_scopes=country_scopes,
                    html=public_source,
                    source_url_override=primary_url,
                    content_type="html",
                )
            except Exception:
                recovered = None
            if recovered is not None:
                recovered_valid = sum(
                    row.get("machine_extraction_status") in {
                        "article_extracted",
                        "article_extracted_by_title_number_variance",
                    }
                    for row in recovered["scopes"]
                )
                parsed_valid = sum(
                    row.get("machine_extraction_status") in {
                        "article_extracted",
                        "article_extracted_by_title_number_variance",
                    }
                    for row in parsed["scopes"]
                )
                if recovered_valid > parsed_valid:
                    parsed = recovered
                    parsed["source_recovery_method"] = (
                        "official_public_slov_lex_page_after_static_non_substantive"
                    )

        parsed["machine_extraction_status"] = (
            "completed"
            if all(
                row.get("machine_extraction_status") in {
                    "article_extracted",
                    "article_extracted_by_title_number_variance",
                }
                for row in parsed["scopes"]
            )
            else "completed_with_scope_recovery_blockers"
        )
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
        "schema_version": 2,
        "dataset_release": "sk-treaty-article-machine-extraction-2026-08-19.4",
        "source_country": "SK",
        "relationship_count": 75,
        "scope_count": 225,
        "policy": {
            "official_primary_text_only": True,
            "income_title_validation_required": True,
            "article_number_is_secondary_to_validated_income_title": True,
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
    valid_statuses = {
        "article_extracted",
        "article_extracted_by_title_number_variance",
    }
    return {
        "schema_version": 2,
        "dataset_release": payload["dataset_release"],
        "relationship_count": payload["relationship_count"],
        "scope_count": payload["scope_count"],
        "article_extracted_scopes": sum(
            row.get("machine_extraction_status") in valid_statuses
            for row in scopes
        ),
        "number_variance_scopes": sum(
            row.get("machine_extraction_status")
            == "article_extracted_by_title_number_variance"
            for row in scopes
        ),
        "title_mismatch_scopes": sum(
            row.get("machine_extraction_status")
            == "article_extracted_title_mismatch_requires_resolution"
            for row in scopes
        ),
        "unresolved_article_scopes": sum(
            row.get("machine_extraction_status") == "validated_article_not_resolved"
            for row in scopes
        ),
        "non_standard_source_scopes": sum(
            row.get("machine_extraction_status") == "non_standard_primary_source_pending"
            for row in scopes
        ),
        "non_substantive_article_scopes": sum(
            row.get("machine_extraction_status")
            == "article_extracted_non_substantive_requires_recovery"
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
    print("Number variances:", summary["number_variance_scopes"])
    print("Title mismatches:", summary["title_mismatch_scopes"])
    print("Unresolved articles:", summary["unresolved_article_scopes"])
    print("Non-standard sources:", summary["non_standard_source_scopes"])


if __name__ == "__main__":
    main()
