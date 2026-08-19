from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

STATUS_PATH = SK_DIR / "mli_relationship_status_inventory.json"
PROFILE_PATH = SK_DIR / "mli_wht_relevance_profile.json"
OUTPUT_PATH = SK_DIR / "mli_notice_review_queue.json"
SUMMARY_PATH = SK_DIR / "mli_notice_review_queue_summary.json"

INCOME_TYPES = ("dividend", "interest", "royalty")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _notice_url(notice: str) -> str:
    number, year = notice.split("/", 1)
    return (
        "https://www.slov-lex.sk/ezbierky/pravne-predpisy/"
        f"SK/ZZ/{year}/{number}/"
    )


def _candidate_articles(
    profile: dict[str, Any],
    income_type: str,
) -> list[str]:
    result: list[str] = []
    for article, detail in profile["articles"].items():
        if (
            detail.get("can_change_result") is True
            and income_type in detail.get("income_types", [])
        ):
            result.append(article)
    return sorted(result, key=int)


def build_queue() -> dict[str, Any]:
    status = _load(STATUS_PATH)
    profile = _load(PROFILE_PATH)

    if status["source_country"] != "SK":
        raise ValueError("Expected Slovak MLI relationship status inventory.")
    if status["relationship_count"] != 46:
        raise ValueError("Expected 46 MLI relationships.")
    if len(status["relationships"]) != 46:
        raise ValueError("MLI relationship status inventory row count mismatch.")
    if profile["policy"].get("pair_specific_matching_required") is not True:
        raise ValueError("Pair-specific MLI matching must remain mandatory.")

    relationships: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []

    for row in status["relationships"]:
        notice = row["slovak_notice"]
        notice_url = _notice_url(notice)
        relationship = {
            "recipient_country": row["recipient_country"],
            "recipient_country_name": row["recipient_country_name"],
            "slovak_notice": notice,
            "slov_lex_notice_url": notice_url,
            "correction_notice": row.get("correction_notice"),
            "correction_notice_url": (
                _notice_url(row["correction_notice"])
                if row.get("correction_notice")
                else None
            ),
            "mf_sr_modification_effective_from": (
                row["mf_sr_modification_effective_from"]
            ),
            "substantive_matching_status": "pending_notice_review",
            "wht_effective_date": None,
            "wht_effective_date_status": "pending_notice_review",
            "runtime_release": False,
        }
        relationships.append(relationship)

        for income_type in INCOME_TYPES:
            scopes.append({
                "packet_id": (
                    f"SK-{row['recipient_country']}-{income_type}-MLI-REVIEW"
                ),
                "source_country": "SK",
                "recipient_country": row["recipient_country"],
                "income_type": income_type,
                "slovak_notice": notice,
                "slov_lex_notice_url": notice_url,
                "candidate_result_changing_articles": _candidate_articles(
                    profile,
                    income_type,
                ),
                "substantive_matching_status": "pending_notice_review",
                "wht_effective_date": None,
                "wht_effective_date_status": "pending_notice_review",
                "review_ready": False,
                "human_review_status": "not_started",
                "approval_eligible": False,
                "runtime_status": "not_released",
            })

    if len({row["recipient_country"] for row in relationships}) != 46:
        raise ValueError("Duplicate MLI relationship country codes detected.")
    if len(scopes) != 138:
        raise ValueError(f"Expected 138 MLI scopes, found {len(scopes)}.")
    if len({row["packet_id"] for row in scopes}) != 138:
        raise ValueError("Duplicate MLI scope packet IDs detected.")
    if any(
        row["review_ready"]
        or row["approval_eligible"]
        or row["runtime_status"] != "not_released"
        for row in scopes
    ):
        raise ValueError("MLI notice review queue must remain fail-closed.")

    return {
        "schema_version": 1,
        "dataset_release": "sk-mli-notice-review-queue-2026-08-19.1",
        "source_country": "SK",
        "relationship_count": 46,
        "scope_count": 138,
        "policy": {
            "fail_closed": True,
            "mf_sr_modification_effective_date_is_not_wht_effective_date": True,
            "wht_effective_date_requires_notice_review": True,
            "substantive_article_matching_requires_notice_review": True,
            "human_review_starts_only_after_all_machine_evidence_is_ready": True,
            "runtime_release": False,
        },
        "relationships": relationships,
        "scopes": scopes,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    relationships = payload["relationships"]
    scopes = payload["scopes"]
    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "relationship_count": len(relationships),
        "scope_count": len(scopes),
        "notice_urls_ready": sum(bool(row["slov_lex_notice_url"]) for row in relationships),
        "correction_notice_relationship_count": sum(
            bool(row["correction_notice"]) for row in relationships
        ),
        "substantive_matching_completed_relationships": sum(
            row["substantive_matching_status"] == "completed"
            for row in relationships
        ),
        "wht_effective_dates_completed_relationships": sum(
            row["wht_effective_date_status"] == "confirmed"
            for row in relationships
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
    print("MLI relationships:", summary["relationship_count"])
    print("MLI scopes:", summary["scope_count"])
    print("Notice URLs ready:", summary["notice_urls_ready"])
    print(
        "Correction-notice relationships:",
        summary["correction_notice_relationship_count"],
    )
    print("Review-ready scopes:", summary["review_ready_scopes"])


if __name__ == "__main__":
    main()
