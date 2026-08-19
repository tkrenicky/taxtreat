from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

INSTRUMENTS_PATH = SK_DIR / "treaty_instrument_inventory.json"
OUTPUT_PATH = SK_DIR / "treaty_source_review_queue.json"
SUMMARY_PATH = SK_DIR / "treaty_source_review_queue_summary.json"

INCOME_ARTICLES = {
    "dividend": 10,
    "interest": 11,
    "royalty": 12,
}

PUBLICATION_RE = re.compile(r"^(\d+)/(\d{4})$")

OFFICIAL_PRIMARY_SOURCE_OVERRIDES = {
    "TW": {
        "url": (
            "https://www.mfsr.sk/files/archiv/financny-spravodajca/"
            "3497/63/FS_09_2011.pdf"
        ),
        "status": "official_mfsr_financial_bulletin_pdf_ready",
        "publication": "FS 9/2011 ozn. č. 31",
    },
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _slov_lex_publication_url(publication: str) -> str | None:
    match = PUBLICATION_RE.fullmatch(publication.strip())
    if match is None:
        return None
    number, year = match.groups()
    return (
        "https://www.slov-lex.sk/ezbierky/pravne-predpisy/"
        f"SK/ZZ/{year}/{number}/"
    )


def build_queue() -> dict[str, Any]:
    instruments = _load(INSTRUMENTS_PATH)
    relationships = instruments["relationships"]

    if len(relationships) != 75:
        raise ValueError("Expected 75 Slovak treaty relationships.")

    relationship_rows: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []

    for source in relationships:
        country = source["recipient_country"]
        publication = source["treaty_publication"]
        override = OFFICIAL_PRIMARY_SOURCE_OVERRIDES.get(country)
        if override:
            url = override["url"]
            source_status = override["status"]
            source_ready = True
        else:
            url = _slov_lex_publication_url(publication)
            source_ready = url is not None
            source_status = (
                "official_slov_lex_url_ready"
                if source_ready
                else "non_standard_primary_source_resolution_required"
            )

        relationship = {
            "recipient_country": country,
            "recipient_country_name": source["recipient_country_name"],
            "treaty_publication": publication,
            "treaty_valid_from": source["treaty_valid_from"],
            "official_primary_text_url": url,
            "primary_text_source_status": source_status,
            "instrument_flags": source.get("instrument_flags", []),
            "risk_reasons": source.get("risk_reasons", []),
            "mli_listed_modified": source["mli_listed_modified"],
            "mli_notice": source.get("mli_notice"),
            "protocol_overlay_status": (
                "pending_instrument_chain_review"
                if "protocol_overlay" in source.get("risk_reasons", [])
                else "not_flagged_in_inventory"
            ),
            "correction_status": (
                "pending_instrument_chain_review"
                if "correction_notice" in source.get("risk_reasons", [])
                else "not_flagged_in_inventory"
            ),
            "runtime_status": "not_released",
        }
        relationship_rows.append(relationship)

        for income_type, article in INCOME_ARTICLES.items():
            blockers = [
                f"article_{article}_semantic_extraction_pending",
                "base_treaty_rule_confirmation_pending",
            ]
            if not source_ready:
                blockers.append("non_standard_primary_source_resolution_pending")
            if source["mli_listed_modified"]:
                blockers.append("pair_specific_mli_overlay_pending")
            if "protocol_overlay" in source.get("risk_reasons", []):
                blockers.append("protocol_overlay_pending")
            if "correction_notice" in source.get("risk_reasons", []):
                blockers.append("correction_notice_pending")

            scopes.append({
                "packet_id": f"SK-{country}-{income_type}-TREATY-SOURCE",
                "source_country": "SK",
                "recipient_country": country,
                "recipient_country_name": source["recipient_country_name"],
                "income_type": income_type,
                "target_article": article,
                "treaty_publication": publication,
                "official_primary_text_url": url,
                "primary_text_source_status": relationship["primary_text_source_status"],
                "semantic_extraction_status": "pending",
                "instrument_chain_status": "pending",
                "review_ready": False,
                "human_review_status": "not_started",
                "approval_eligible": False,
                "runtime_status": "not_released",
                "release_blockers": blockers,
            })

    if len({row["recipient_country"] for row in relationship_rows}) != 75:
        raise ValueError("Duplicate treaty relationship codes detected.")
    if len(scopes) != 225:
        raise ValueError(f"Expected 225 treaty source scopes, found {len(scopes)}.")
    if len({row["packet_id"] for row in scopes}) != 225:
        raise ValueError("Duplicate treaty source packet IDs detected.")
    if any(
        row["review_ready"]
        or row["approval_eligible"]
        or row["runtime_status"] != "not_released"
        for row in scopes
    ):
        raise ValueError("Treaty source review queue must remain fail-closed.")

    return {
        "schema_version": 2,
        "dataset_release": "sk-treaty-source-review-queue-2026-08-19.2",
        "source_country": "SK",
        "relationship_count": 75,
        "scope_count": 225,
        "policy": {
            "official_primary_source_required": True,
            "official_mfsr_financial_bulletin_is_valid_primary_source": True,
            "non_standard_sources_must_not_be_guessed": True,
            "instrument_chain_must_include_protocols_corrections_and_mli": True,
            "human_review_starts_only_after_all_machine_evidence_is_ready": True,
            "runtime_release": False,
        },
        "relationships": relationship_rows,
        "scopes": scopes,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    relationships = payload["relationships"]
    scopes = payload["scopes"]
    return {
        "schema_version": 2,
        "dataset_release": payload["dataset_release"],
        "relationship_count": len(relationships),
        "scope_count": len(scopes),
        "official_slov_lex_urls_ready": sum(
            row["primary_text_source_status"] == "official_slov_lex_url_ready"
            for row in relationships
        ),
        "official_mfsr_bulletin_urls_ready": sum(
            row["primary_text_source_status"]
            == "official_mfsr_financial_bulletin_pdf_ready"
            for row in relationships
        ),
        "unresolved_primary_source_relationships": sum(
            row["primary_text_source_status"]
            == "non_standard_primary_source_resolution_required"
            for row in relationships
        ),
        "semantic_extraction_completed_scopes": sum(
            row["semantic_extraction_status"] == "completed"
            for row in scopes
        ),
        "review_ready_scopes": sum(row["review_ready"] for row in scopes),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_queue()
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Treaty relationships:", summary["relationship_count"])
    print("Treaty scopes:", summary["scope_count"])
    print("Slov-Lex URLs ready:", summary["official_slov_lex_urls_ready"])
    print("MF bulletin URLs ready:", summary["official_mfsr_bulletin_urls_ready"])
    print(
        "Unresolved primary source relationships:",
        summary["unresolved_primary_source_relationships"],
    )
    print("Review-ready scopes:", summary["review_ready_scopes"])


if __name__ == "__main__":
    main()
