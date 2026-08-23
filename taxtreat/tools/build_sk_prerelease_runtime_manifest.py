from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from taxtreat.tools.build_sk_domestic_review_readiness import (
    COOPERATING_SOURCE_PATH,
    cooperating_state_status,
)


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

SEMANTIC_PATH = SK_DIR / "treaty_semantic_candidates.json"
MLI_PATH = SK_DIR / "mli_notice_machine_extraction.json"
COMPLIANCE_PATH = SK_DIR / "compliance_profile_2026.json"
DIVIDEND_MODEL_PATH = SK_DIR / "dividend_domestic_condition_model.json"
DOMESTIC_MODEL_PATH = SK_DIR / "domestic_transaction_condition_model.json"
COOPERATING_SOURCE = COOPERATING_SOURCE_PATH
OUTPUT_PATH = SK_DIR / "prerelease_runtime_manifest.json"
SUMMARY_PATH = SK_DIR / "prerelease_runtime_manifest_summary.json"
HUMAN_REVIEW_COVERAGE_PATH = SK_DIR / "human_review_coverage.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _mli_by_country() -> dict[str, dict[str, Any]]:
    payload = _load(MLI_PATH)
    return {
        row["recipient_country"]: row
        for row in payload["relationships"]
    }


def build_manifest() -> dict[str, Any]:
    semantic = _load(SEMANTIC_PATH)
    compliance = _load(COMPLIANCE_PATH)
    dividend_model = _load(DIVIDEND_MODEL_PATH)
    domestic = _load(DOMESTIC_MODEL_PATH)
    cooperating_source = _load(COOPERATING_SOURCE)
    mli = _mli_by_country()

    if semantic.get("scope_count") != 225:
        raise ValueError("SK semantic evidence must cover 225 scopes.")

    rows: list[dict[str, Any]] = []
    for source in semantic["scopes"]:
        country = source["recipient_country"]
        income = source["income_type"]
        packet_id = source["packet_id"]
        semantic_status = source.get("semantic_status")
        if semantic_status not in {
            "machine_candidate_not_legal_conclusion",
            "machine_candidate_primary_summary_fallback_not_legal_conclusion",
        }:
            raise ValueError(f"{packet_id}: semantic evidence is not machine-ready.")

        mli_row = mli.get(country)
        mli_applicable = mli_row is not None
        if mli_applicable and mli_row.get("machine_extraction_status") != "completed":
            raise ValueError(f"{packet_id}: MLI relationship is not machine-ready.")

        cooperating_status = cooperating_state_status(
            recipient_country=country,
            transaction_date=date(2026, 1, 1),
            source=cooperating_source,
        )
        list_ready = cooperating_status["status"] == "resolved_from_official_annual_list"

        rows.append({
            "scope_key": ["SK", country, income],
            "packet_id": packet_id,
            "source_country": "SK",
            "recipient_country": country,
            "income_type": income,
            "treaty_machine_evidence_status": semantic_status,
            "treaty_source_url": source.get("source_url"),
            "treaty_source_sha256": source.get("source_sha256"),
            "treaty_article": source.get("actual_article"),
            "treaty_semantic_candidate": {
                "rate_candidates": source.get("rate_candidates", []),
                "exclusive_residence_taxation_candidate": bool(
                    source.get("exclusive_residence_taxation_candidate")
                ),
                "beneficial_owner_wording_present": bool(
                    source.get("beneficial_owner_wording_present")
                ),
                "pe_or_fixed_base_carveout_wording_present": bool(
                    source.get("pe_or_fixed_base_carveout_wording_present")
                ),
                "holding_period_candidates": source.get(
                    "holding_period_candidates", []
                ),
                "ownership_linked_rate_candidate_count": int(
                    source.get("ownership_linked_rate_candidate_count") or 0
                ),
                "evidence_quality": source.get(
                    "evidence_quality", "official_primary_source_byte_extracted"
                ),
            },
            "mli_applicable": mli_applicable,
            "mli_machine_evidence_status": (
                mli_row.get("machine_extraction_status") if mli_row else "not_applicable"
            ),
            "mli_notice": mli_row.get("slovak_notice") if mli_row else None,
            "mli_wht_effective_dates": (
                mli_row.get("wht_effective_dates") if mli_row else []
            ),
            "domestic_model": (
                "sk_dividend_section_12_7_c"
                if income == "dividend"
                else "sk_interest_royalty_section_43_and_section_13"
            ),
            "compliance_form": (
                compliance.get("ordinary_corporate_outbound_wht", {})
                .get("notification", {})
                .get("form_code")
            ),
            "compliance_legal_reference": (
                compliance.get("ordinary_corporate_outbound_wht", {})
                .get("notification", {})
                .get("legal_reference")
            ),
            "cooperating_state_status_required": True,
            "cooperating_state_list_ready": list_ready,
            "cooperating_state_status": cooperating_status["status"],
            "is_cooperating_state": cooperating_status["is_cooperating_state"],
            "candidate_only": True,
            "human_review_status": "not_started",
            "approval_eligible": False,
            "runtime_released": False,
        })

    if len(rows) != 225:
        raise ValueError("Expected 225 SK prerelease runtime rows.")
    if len({tuple(row["scope_key"]) for row in rows}) != 225:
        raise ValueError("Duplicate SK runtime scope keys detected.")
    if any(row["approval_eligible"] for row in rows):
        raise ValueError("Prerelease runtime manifest cannot approve legal conclusions.")
    if any(row["runtime_released"] for row in rows):
        raise ValueError("Prerelease runtime manifest cannot release SK runtime.")

    if dividend_model.get("source_country") != "SK":
        raise ValueError("SK dividend domestic model missing.")
    if domestic.get("source_country") != "SK":
        raise ValueError("SK interest/royalty domestic model missing.")

    return {
        "schema_version": 2,
        "dataset_release": "sk-prerelease-runtime-manifest-2026-08-19.2",
        "source_country": "SK",
        "scope_count": 225,
        "policy": {
            "candidate_evidence_only": True,
            "country_specific_domestic_logic_required": True,
            "pair_specific_mli_required": True,
            "czech_runtime_fallback_prohibited": True,
            "human_review_required_before_release": True,
            "cooperating_state_list_required_before_domestic_rate_release": True,
            "semantic_candidates_must_never_be_promoted_without_human_review": True,
            "runtime_release": False,
        },
        "scopes": rows,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["scopes"]
    return {
        "schema_version": 2,
        "dataset_release": payload["dataset_release"],
        "scope_count": len(rows),
        "mli_scopes": sum(row["mli_applicable"] for row in rows),
        "non_mli_scopes": sum(not row["mli_applicable"] for row in rows),
        "primary_summary_fallback_scopes": sum(
            "primary_summary_fallback" in row["treaty_machine_evidence_status"]
            for row in rows
        ),
        "scopes_with_rate_candidates": sum(
            bool(row["treaty_semantic_candidate"]["rate_candidates"])
            for row in rows
        ),
        "exclusive_residence_candidate_scopes": sum(
            row["treaty_semantic_candidate"][
                "exclusive_residence_taxation_candidate"
            ]
            for row in rows
        ),
        "cooperating_state_list_ready_scopes": sum(
            row["cooperating_state_list_ready"] for row in rows
        ),
        "human_reviewed_scopes": _load(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["individually_reviewed_scopes"],
        "pattern_reconciled_scopes": _load(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["pattern_reconciled_scopes"],
        "legal_review_covered_scopes": _load(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["legal_review_covered_scopes"],
        "production_released_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_manifest()
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
