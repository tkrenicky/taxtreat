from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

BATCH_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
)

PACKS = {
    "dividend": (
        BATCH_DIR
        / "batch_01_be_dividend_primary_review_pack.json"
    ),
    "interest": (
        BATCH_DIR
        / "batch_01_be_interest_primary_review_pack.json"
    ),
    "royalty": (
        BATCH_DIR
        / "batch_01_be_royalty_primary_review_pack.json"
    ),
}

OUTPUT = (
    BATCH_DIR
    / "batch_01_be_consolidated_primary_review_decisions.json"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_scope_decision(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_id": payload["packet_id"],
        "recipient_country": payload["recipient_country"],
        "income_type": payload["income_type"],
        "review_row_sha256": payload["review_row_sha256"],
        "source_material": {
            "treaty_source_id": payload["treaty"].get(
                "source_id"
            ),
            "protocol_source_ids": [
                document.get("source_id")
                for document in payload[
                    "protocols"
                ].get("documents", [])
                if document.get("source_id")
            ],
            "domestic_source_id": payload[
                "domestic_and_eu"
            ].get(
                "domestic_rate_candidate",
                {},
            ).get("source_id"),
            "directive_source_id": payload[
                "domestic_and_eu"
            ].get(
                "relief_candidate",
                {},
            ).get("directive_source_id"),
            "mli_source_ids": [
                effect.get("source_page_id")
                for effect in payload.get(
                    "mli_effects",
                    [],
                )
                if effect.get("source_page_id")
            ],
        },
        "review_questions": [
            {
                "question": question,
                "answer": None,
                "legal_reasoning": None,
                "supporting_source_ids": [],
            }
            for question in payload["review_questions"]
        ],
        "confirmations": {
            "treaty_rate_candidates_confirmed": None,
            "beneficial_owner_requirement_confirmed": None,
            "protocol_effects_confirmed": None,
            "mli_effects_confirmed": None,
            "domestic_rate_confirmed": None,
            "eu_relief_confirmed": None,
            "effective_date_confirmed": None,
            "anti_abuse_review_completed": None,
        },
        "proposed_rule_snapshot": None,
        "reviewer": {
            "reviewer_id": None,
            "reviewed_at": None,
        },
        "review_outcome": None,
        "status": "awaiting_primary_review",
        "promotable_to_active_rules": False,
    }


def build_consolidated_review() -> dict[str, Any]:
    scopes = []

    for income_type in (
        "dividend",
        "interest",
        "royalty",
    ):
        payload = read_json(PACKS[income_type])
        scopes.append(build_scope_decision(payload))

    return {
        "schema_version": 1,
        "dataset_release": (
            "batch-01-be-consolidated-primary-review-"
            "2026-08-06.1"
        ),
        "country": "BE",
        "country_name": "Belgie",
        "scope_count": 3,
        "policy": {
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "automatic_legal_confirmation_prohibited": True,
            "all_scopes_fail_closed": True,
        },
        "scopes": scopes,
        "summary": {
            "awaiting_primary_review": 3,
            "awaiting_independent_approval": 0,
            "returned_for_correction": 0,
            "promotable_scopes": 0,
        },
    }


def main() -> None:
    payload = build_consolidated_review()

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

    print("Belgium consolidated primary review created.")
    print("Output:", OUTPUT.relative_to(ROOT))
    print("Scopes:", payload["scope_count"])
    print(
        "Awaiting primary review:",
        payload["summary"]["awaiting_primary_review"],
    )
    print(
        "Promotable scopes:",
        payload["summary"]["promotable_scopes"],
    )


if __name__ == "__main__":
    main()
