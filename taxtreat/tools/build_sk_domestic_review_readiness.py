from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

DOMESTIC_PATH = SK_DIR / "domestic_wht_candidates.json"
COOPERATING_SOURCE_PATH = SK_DIR / "cooperating_states_source_2026.json"
OUTPUT_PATH = SK_DIR / "domestic_review_readiness.json"
SUMMARY_PATH = SK_DIR / "domestic_review_readiness_summary.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def cooperating_state_status(
    *,
    recipient_country: str,
    transaction_date: date,
    source: dict[str, Any],
) -> dict[str, Any]:
    official = source["official_list"]
    valid_from = _parse_date(official["valid_from"])
    valid_to = _parse_date(official["valid_to"])

    if not (valid_from <= transaction_date <= valid_to):
        return {
            "status": "blocked_no_valid_annual_list_for_transaction_date",
            "is_cooperating_state": None,
            "is_non_cooperative_state": None,
        }

    codes = source.get("cooperating_state_codes")
    if codes is None:
        return {
            "status": "blocked_official_annual_list_body_not_ingested",
            "is_cooperating_state": None,
            "is_non_cooperative_state": None,
        }

    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate country codes in cooperating-state list.")

    code = recipient_country.upper()
    is_cooperating = code in set(codes)
    return {
        "status": "resolved_from_official_annual_list",
        "is_cooperating_state": is_cooperating,
        "is_non_cooperative_state": not is_cooperating,
    }


def withholding_rate_candidate(
    *,
    recipient_country: str,
    transaction_date: date,
    source: dict[str, Any],
    domestic: dict[str, Any],
) -> dict[str, Any]:
    status = cooperating_state_status(
        recipient_country=recipient_country,
        transaction_date=transaction_date,
        source=source,
    )

    if status["is_non_cooperative_state"] is None:
        return {
            **status,
            "domestic_wht_rate_candidate": None,
            "rate_status": "blocked",
        }

    common = domestic["common"]
    rate = (
        common["non_cooperative_state_rate_percent"]
        if status["is_non_cooperative_state"]
        else common["standard_withholding_rate_percent"]
    )
    return {
        **status,
        "domestic_wht_rate_candidate": rate,
        "rate_status": "machine_candidate_not_legal_conclusion",
    }


def build_readiness() -> dict[str, Any]:
    domestic = _load(DOMESTIC_PATH)
    source = _load(COOPERATING_SOURCE_PATH)

    if domestic["source_country"] != "SK":
        raise ValueError("Expected Slovak domestic WHT candidate model.")
    if source["source_country"] != "SK":
        raise ValueError("Expected Slovak cooperating-state source model.")

    standard_rate = domestic["common"]["standard_withholding_rate_percent"]
    protective_rate = domestic["common"]["non_cooperative_state_rate_percent"]
    if (standard_rate, protective_rate) != (19, 35):
        raise ValueError("Unexpected Slovak domestic WHT candidate rates.")

    list_complete = source.get("cooperating_state_codes") is not None
    blocker = None if list_complete else "official_2026_cooperating_state_list_body_pending_ingestion"

    return {
        "schema_version": 1,
        "dataset_release": "sk-domestic-review-readiness-2026-08-19.1",
        "source_country": "SK",
        "domestic_rates": {
            "standard_rate_percent": standard_rate,
            "non_cooperative_state_rate_percent": protective_rate,
        },
        "cooperating_state_list": {
            "valid_from": source["official_list"]["valid_from"],
            "valid_to": source["official_list"]["valid_to"],
            "mf_document_id": source["official_list"]["mf_document_id"],
            "ingestion_complete": list_complete,
            "blocker": blocker,
        },
        "policy": {
            "non_cooperative_status_is_date_specific": True,
            "non_treaty_partner_does_not_equal_non_cooperative_state": True,
            "35_percent_rate_requires_resolved_non_cooperative_status": True,
            "incomplete_positive_list_blocks_rate_selection": True,
            "machine_candidate_is_not_human_approval": True,
            "runtime_release": False,
        },
        "review_ready": list_complete,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "runtime_status": "not_released",
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "cooperating_state_list_ingestion_complete": payload[
            "cooperating_state_list"
        ]["ingestion_complete"],
        "domestic_rate_branch_machine_ready": payload["review_ready"],
        "human_reviewed": False,
        "production_released": False,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_readiness()
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
