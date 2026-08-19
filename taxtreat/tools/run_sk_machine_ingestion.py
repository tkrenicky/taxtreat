from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.tools.build_sk_mli_notice_review_queue import (
    OUTPUT_PATH as MLI_QUEUE_OUTPUT,
    SUMMARY_PATH as MLI_QUEUE_SUMMARY,
    build_queue as build_mli_queue,
    build_summary as build_mli_queue_summary,
)
from taxtreat.tools.build_sk_prerelease_runtime_manifest import (
    OUTPUT_PATH as RUNTIME_MANIFEST_OUTPUT,
    SUMMARY_PATH as RUNTIME_MANIFEST_SUMMARY,
    build_manifest as build_runtime_manifest,
    build_summary as build_runtime_manifest_summary,
)
from taxtreat.tools.build_sk_treaty_semantic_candidates import (
    OUTPUT_PATH as SEMANTIC_OUTPUT,
    SUMMARY_PATH as SEMANTIC_SUMMARY,
    build_candidates,
    build_summary as build_semantic_summary,
)
from taxtreat.tools.build_sk_treaty_source_review_queue import (
    OUTPUT_PATH as TREATY_QUEUE_OUTPUT,
    SUMMARY_PATH as TREATY_QUEUE_SUMMARY,
    build_queue as build_treaty_queue,
    build_summary as build_treaty_queue_summary,
)
from taxtreat.tools.extract_sk_mli_notices import (
    OUTPUT_PATH as MLI_EXTRACTION_OUTPUT,
    PROFILE_PATH,
    STATUS_PATH,
    SUMMARY_PATH as MLI_EXTRACTION_SUMMARY,
    _fetch as fetch_mli,
    _static_notice_url,
    build_summary as build_mli_extraction_summary,
    parse_notice,
)
from taxtreat.tools.extract_sk_treaty_articles import (
    OFFICIAL_PDF_OVERRIDES,
    OUTPUT_PATH as TREATY_EXTRACTION_OUTPUT,
    SUMMARY_PATH as TREATY_EXTRACTION_SUMMARY,
    _fetch as fetch_treaty,
    _static_source_url,
    build_summary as build_treaty_extraction_summary,
    parse_treaty,
)


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
RUN_SUMMARY_PATH = SK_DIR / "machine_ingestion_run_summary.json"
TW_FALLBACK_PATH = SK_DIR / "tw_primary_summary_fallback.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _mli_failure_row(source: dict[str, Any], url: str, problem: Exception) -> dict[str, Any]:
    return {
        "recipient_country": source["recipient_country"],
        "recipient_country_name": source["recipient_country_name"],
        "slovak_notice": source["slovak_notice"],
        "source_url": url,
        "machine_extraction_status": "fetch_or_parse_failed",
        "error_type": type(problem).__name__,
        "error_message": str(problem)[:500],
        "wht_effective_date_status": "blocked_fetch_or_parse_failed",
        "substantive_matching_status": "blocked_fetch_or_parse_failed",
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def _run_mli_extraction() -> dict[str, Any]:
    status = _load(STATUS_PATH)
    profile = _load(PROFILE_PATH)
    rows: list[dict[str, Any]] = []

    for source in status["relationships"]:
        url = _static_notice_url(source["slovak_notice"])
        try:
            fetched = fetch_mli(url)
            row = parse_notice(
                recipient_country=source["recipient_country"],
                recipient_country_name=source["recipient_country_name"],
                notice=source["slovak_notice"],
                html=fetched.html,
                profile=profile,
            )
            row["machine_extraction_status"] = "completed"
        except Exception as problem:
            row = _mli_failure_row(source, url, problem)
        rows.append(row)

    payload = {
        "schema_version": 1,
        "dataset_release": "sk-mli-notice-machine-extraction-2026-08-19.2",
        "source_country": "SK",
        "relationship_count": 46,
        "policy": {
            "official_static_slov_lex_only": True,
            "per_pair_failure_is_fail_closed_not_batch_fatal": True,
            "machine_extraction_is_not_human_approval": True,
            "runtime_release": False,
        },
        "relationships": rows,
    }
    if len(rows) != 46:
        raise ValueError("MLI resilient ingestion lost relationship rows.")
    _write(MLI_EXTRACTION_OUTPUT, payload)
    _write(MLI_EXTRACTION_SUMMARY, build_mli_extraction_summary(payload))
    return payload


def _treaty_failure_scope(source_scope: dict[str, Any], problem: Exception) -> dict[str, Any]:
    return {
        "packet_id": source_scope["packet_id"],
        "source_country": "SK",
        "recipient_country": source_scope["recipient_country"],
        "income_type": source_scope["income_type"],
        "machine_extraction_status": "fetch_or_parse_failed",
        "error_type": type(problem).__name__,
        "error_message": str(problem)[:500],
        "review_ready": False,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def _resolve_treaty_source(source: dict[str, Any]) -> tuple[str | None, str]:
    country = source["recipient_country"]
    primary_url = source.get("official_primary_text_url")

    pdf_override = OFFICIAL_PDF_OVERRIDES.get(country)
    if pdf_override:
        return pdf_override, "pdf"

    if primary_url is None:
        return None, "unknown"

    if primary_url.lower().endswith(".pdf"):
        return primary_url, "pdf"

    return _static_source_url(primary_url), "html"


def _taiwan_primary_summary_rows(
    source: dict[str, Any],
    country_scopes: list[dict[str, Any]],
    problem: Exception,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fallback = _load(TW_FALLBACK_PATH)
    if fallback.get("recipient_country") != "TW":
        raise ValueError("Taiwan fallback evidence file is not scoped to TW.")
    primary = fallback["primary_source"]
    if primary.get("url") != source.get("official_primary_text_url"):
        raise ValueError("Taiwan fallback source URL does not match treaty queue provenance.")

    relationship = {
        "recipient_country": "TW",
        "recipient_country_name": source["recipient_country_name"],
        "treaty_publication": source["treaty_publication"],
        "source_url": primary["url"],
        "source_content_type": "pdf",
        "source_snapshot_path": str(TW_FALLBACK_PATH.relative_to(ROOT)),
        "machine_extraction_status": "completed_primary_summary_fallback",
        "primary_pdf_fetch_error_type": type(problem).__name__,
        "primary_pdf_fetch_error_message": str(problem)[:500],
        "evidence_quality": "official_primary_source_summary_fallback_not_byte_exact",
        "human_review_status": "not_started",
        "runtime_status": "not_released",
    }

    rows: list[dict[str, Any]] = []
    for scope in country_scopes:
        income = scope["income_type"]
        evidence = fallback["scopes"][income]
        rows.append({
            "packet_id": scope["packet_id"],
            "source_country": "SK",
            "recipient_country": "TW",
            "income_type": income,
            "expected_article": str({"dividend": 10, "interest": 11, "royalty": 12}[income]),
            "actual_article": evidence["article"],
            "article_resolution_status": "official_primary_summary_fallback_after_pdf_timeout",
            "article_text": None,
            "article_text_sha256": None,
            "source_url": primary["url"],
            "source_sha256": None,
            "source_snapshot_path": str(TW_FALLBACK_PATH.relative_to(ROOT)),
            "primary_summary_evidence": evidence,
            "machine_extraction_status": "article_evidence_primary_summary_fallback",
            "title_validation_status": "expected_income_title_matched_from_primary_summary",
            "review_ready": False,
            "human_review_status": "not_started",
            "approval_eligible": False,
            "runtime_status": "not_released",
        })
    return relationship, rows


def _run_treaty_extraction(treaty_queue: dict[str, Any]) -> dict[str, Any]:
    by_country_scopes: dict[str, list[dict[str, Any]]] = {}
    for scope in treaty_queue["scopes"]:
        by_country_scopes.setdefault(scope["recipient_country"], []).append(scope)

    relationships: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []

    for source in treaty_queue["relationships"]:
        country = source["recipient_country"]
        country_scopes = by_country_scopes[country]
        url, content_type = _resolve_treaty_source(source)

        if url is None:
            relationships.append({
                "recipient_country": country,
                "recipient_country_name": source["recipient_country_name"],
                "treaty_publication": source["treaty_publication"],
                "source_url": None,
                "machine_extraction_status": "non_standard_primary_source_pending",
                "human_review_status": "not_started",
                "runtime_status": "not_released",
            })
            for source_scope in country_scopes:
                scopes.append({
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

        try:
            source_bytes = fetch_treaty(url)
            parsed = parse_treaty(
                source_relationship=source,
                source_scopes=country_scopes,
                html=source_bytes,
                source_url_override=url,
                content_type=content_type,
            )
            relationship_row = {
                key: value for key, value in parsed.items() if key != "scopes"
            }
            relationship_row["machine_extraction_status"] = "completed"
            relationships.append(relationship_row)
            scopes.extend(parsed["scopes"])
        except Exception as problem:
            if country == "TW" and TW_FALLBACK_PATH.exists():
                relationship_row, scope_rows = _taiwan_primary_summary_rows(
                    source,
                    country_scopes,
                    problem,
                )
                relationships.append(relationship_row)
                scopes.extend(scope_rows)
                continue

            relationships.append({
                "recipient_country": country,
                "recipient_country_name": source["recipient_country_name"],
                "treaty_publication": source["treaty_publication"],
                "source_url": url,
                "source_content_type": content_type,
                "machine_extraction_status": "fetch_or_parse_failed",
                "error_type": type(problem).__name__,
                "error_message": str(problem)[:500],
                "human_review_status": "not_started",
                "runtime_status": "not_released",
            })
            scopes.extend(
                _treaty_failure_scope(source_scope, problem)
                for source_scope in country_scopes
            )

    payload = {
        "schema_version": 3,
        "dataset_release": "sk-treaty-article-machine-extraction-2026-08-19.4",
        "source_country": "SK",
        "relationship_count": 75,
        "scope_count": 225,
        "policy": {
            "official_primary_text_only": True,
            "official_html_and_pdf_sources_supported": True,
            "taiwan_primary_summary_fallback_is_explicit_not_byte_exact": True,
            "per_pair_failure_is_fail_closed_not_batch_fatal": True,
            "machine_extraction_is_not_semantic_legal_approval": True,
            "runtime_release": False,
        },
        "relationships": relationships,
        "scopes": scopes,
    }
    if len(relationships) != 75 or len(scopes) != 225:
        raise ValueError("Treaty resilient ingestion lost relationship/scope rows.")
    _write(TREATY_EXTRACTION_OUTPUT, payload)
    _write(TREATY_EXTRACTION_SUMMARY, build_treaty_extraction_summary(payload))
    return payload


def run() -> dict[str, Any]:
    mli_queue = build_mli_queue()
    _write(MLI_QUEUE_OUTPUT, mli_queue)
    _write(MLI_QUEUE_SUMMARY, build_mli_queue_summary(mli_queue))

    treaty_queue = build_treaty_queue()
    _write(TREATY_QUEUE_OUTPUT, treaty_queue)
    _write(TREATY_QUEUE_SUMMARY, build_treaty_queue_summary(treaty_queue))

    mli_extraction = _run_mli_extraction()
    treaty_extraction = _run_treaty_extraction(treaty_queue)

    semantic = build_candidates()
    _write(SEMANTIC_OUTPUT, semantic)
    _write(SEMANTIC_SUMMARY, build_semantic_summary(semantic))

    runtime_manifest = build_runtime_manifest()
    runtime_manifest_summary = build_runtime_manifest_summary(runtime_manifest)
    _write(RUNTIME_MANIFEST_OUTPUT, runtime_manifest)
    _write(RUNTIME_MANIFEST_SUMMARY, runtime_manifest_summary)

    mli_completed = sum(
        row.get("machine_extraction_status") == "completed"
        for row in mli_extraction["relationships"]
    )
    treaty_completed_statuses = {"completed", "completed_primary_summary_fallback"}
    treaty_completed = sum(
        row.get("machine_extraction_status") in treaty_completed_statuses
        for row in treaty_extraction["relationships"]
    )
    semantic_candidate_statuses = {
        "machine_candidate_not_legal_conclusion",
        "machine_candidate_primary_summary_fallback_not_legal_conclusion",
    }
    semantic_candidates = sum(
        row.get("semantic_status") in semantic_candidate_statuses
        for row in semantic["scopes"]
    )

    summary = {
        "schema_version": 4,
        "source_country": "SK",
        "mli_relationships_total": 46,
        "mli_relationships_machine_extracted": mli_completed,
        "mli_relationships_blocked": 46 - mli_completed,
        "treaty_relationships_total": 75,
        "treaty_relationships_machine_evidence_ready": treaty_completed,
        "treaty_relationships_blocked": 75 - treaty_completed,
        "treaty_primary_summary_fallback_relationships": sum(
            row.get("machine_extraction_status") == "completed_primary_summary_fallback"
            for row in treaty_extraction["relationships"]
        ),
        "treaty_scopes_total": 225,
        "semantic_candidate_scopes": semantic_candidates,
        "prerelease_runtime_manifest_scopes": runtime_manifest_summary["scope_count"],
        "prerelease_runtime_manifest_released_scopes": runtime_manifest_summary[
            "production_released_scopes"
        ],
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "fail_closed": True,
    }
    _write(RUN_SUMMARY_PATH, summary)
    return summary


def main() -> None:
    summary = run()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
