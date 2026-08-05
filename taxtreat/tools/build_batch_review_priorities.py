from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DOSSIERS = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_country_dossiers.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_priorities.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_scope_flags(scope: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []

    rates = [
        candidate.get("rate")
        for candidate in scope.get("rate_candidates", [])
    ]

    if not rates:
        flags.append(
            {
                "severity": "high",
                "code": "no_rate_candidate",
                "message": (
                    "No treaty rate candidate was extracted; the article "
                    "must be reviewed manually."
                ),
            }
        )

    if len(rates) > 1:
        flags.append(
            {
                "severity": "medium",
                "code": "multiple_rate_candidates",
                "message": (
                    "Multiple treaty rates require confirmation of the "
                    "applicable categories and conditions."
                ),
            }
        )

    if rates.count(0.0) > 1:
        flags.append(
            {
                "severity": "high",
                "code": "multiple_zero_rate_candidates",
                "message": (
                    "Multiple zero-rate candidates may represent separate "
                    "exemptions or duplicate extraction."
                ),
            }
        )

    if 0.0 in rates:
        flags.append(
            {
                "severity": "medium",
                "code": "treaty_zero_rate",
                "message": (
                    "A zero-rate treaty candidate must be tied to its "
                    "precise legal conditions or exemption category."
                ),
            }
        )

    if len(scope.get("protocol_documents", [])) > 1:
        flags.append(
            {
                "severity": "high",
                "code": "multiple_protocol_documents",
                "message": (
                    "Multiple protocol documents require chronological "
                    "consolidation and confirmation of cumulative effects."
                ),
            }
        )

    if scope.get("protocol_documents") and not scope.get(
        "protocol_scope_effects"
    ):
        flags.append(
            {
                "severity": "high",
                "code": "protocol_without_scope_effect",
                "message": (
                    "A protocol exists but no income-specific effect was "
                    "linked to this scope."
                ),
            }
        )

    if not scope.get("mli_effects"):
        flags.append(
            {
                "severity": "medium",
                "code": "no_mli_effect_recorded",
                "message": (
                    "No MLI withholding-tax effect is recorded; treaty "
                    "coverage and effective dates require confirmation."
                ),
            }
        )

    if scope["income_type"] == "royalty" and len(rates) > 1:
        flags.append(
            {
                "severity": "high",
                "code": "royalty_category_mapping_required",
                "message": (
                    "Royalty rates must be mapped to the precise categories "
                    "of rights, property or information."
                ),
            }
        )

    if scope["income_type"] == "interest" and rates == [0.0]:
        flags.append(
            {
                "severity": "high",
                "code": "interest_full_exemption_candidate",
                "message": (
                    "The extracted interest result is 0%; confirm whether "
                    "the article grants a general exemption or only "
                    "category-specific exemptions."
                ),
            }
        )

    if scope["income_type"] == "dividend" and 20.0 in rates:
        flags.append(
            {
                "severity": "high",
                "code": "dividend_20_percent_candidate",
                "message": (
                    "The 20% dividend candidate is unusual for the batch "
                    "and requires precise category and historical-effect "
                    "confirmation."
                ),
            }
        )

    return flags


def priority_score(flags: list[dict[str, str]]) -> int:
    weights = {
        "high": 5,
        "medium": 2,
        "low": 1,
    }

    return sum(weights[item["severity"]] for item in flags)


def build_priorities() -> dict[str, Any]:
    dossiers = read_json(DOSSIERS)

    scopes = []

    for country in dossiers["countries"]:
        for scope in country["scopes"]:
            flags = build_scope_flags(scope)

            scopes.append(
                {
                    "packet_id": scope["packet_id"],
                    "recipient_country": country[
                        "recipient_country"
                    ],
                    "recipient_country_name": country[
                        "recipient_country_name"
                    ],
                    "income_type": scope["income_type"],
                    "rate_candidates": [
                        item.get("rate")
                        for item in scope["rate_candidates"]
                    ],
                    "protocol_document_count": len(
                        scope["protocol_documents"]
                    ),
                    "mli_effect_count": len(
                        scope["mli_effects"]
                    ),
                    "flags": flags,
                    "priority_score": priority_score(flags),
                    "review_status": (
                        "awaiting_primary_review"
                    ),
                }
            )

    scopes.sort(
        key=lambda item: (
            -item["priority_score"],
            item["recipient_country"],
            item["income_type"],
        )
    )

    high_priority = [
        item
        for item in scopes
        if item["priority_score"] >= 7
    ]

    medium_priority = [
        item
        for item in scopes
        if 3 <= item["priority_score"] < 7
    ]

    low_priority = [
        item
        for item in scopes
        if item["priority_score"] < 3
    ]

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-priorities-2026-08-05.1"
        ),
        "policy": {
            "priority_is_not_legal_conclusion": True,
            "human_review_required": True,
            "fail_closed": True,
        },
        "summary": {
            "scopes": len(scopes),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "completed_primary_reviews": 0,
        },
        "review_order": scopes,
    }

    if len(scopes) != 30:
        raise ValueError(
            f"Expected 30 scopes, found {len(scopes)}."
        )

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    payload = build_priorities()

    print("Batch review priorities created.")
    print("Scopes:", payload["summary"]["scopes"])
    print(
        "High priority:",
        payload["summary"]["high_priority"],
    )
    print(
        "Medium priority:",
        payload["summary"]["medium_priority"],
    )
    print(
        "Low priority:",
        payload["summary"]["low_priority"],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
