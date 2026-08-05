from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

BASE = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_base_candidates.json"
)

MATRIX = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_belgium_worksheet.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_worksheet() -> dict[str, Any]:
    base = read_json(BASE)
    matrix = read_json(MATRIX)

    base_rows = {
        item["income_type"]: item
        for item in base["scopes"]
        if item["recipient_country"] == "BE"
    }

    matrix_rows = {
        item["income_type"]: item
        for item in matrix["rows"]
        if item["recipient_country"] == "BE"
    }

    if set(base_rows) != {"dividend", "interest", "royalty"}:
        raise ValueError("Expected three Belgian base treaty scopes.")

    scopes = []

    for income_type in ("dividend", "interest", "royalty"):
        base_row = base_rows[income_type]
        matrix_row = matrix_rows[income_type]

        scope = {
            "packet_id": matrix_row["packet_id"],
            "income_type": income_type,
            "treaty_publication": base_row[
                "base_treaty_publication"
            ],
            "treaty_source_id": base_row[
                "base_treaty_source_id"
            ],
            "article_number": base_row["article_number"],
            "article_title": base_row["article_title"],
            "article_text": base_row["article_text"],
            "article_text_sha256": base_row[
                "article_text_sha256"
            ],
            "candidate_rates": base_row["rate_candidates"],
            "discarded_rate_candidates": base_row[
                "discarded_rate_candidates"
            ],
            "domestic_rate_candidate": matrix_row[
                "domestic_and_eu"
            ]["domestic_rate_candidate"],
            "eu_relief_candidate": matrix_row[
                "domestic_and_eu"
            ]["relief_candidate"],
            "protocol_documents": matrix_row[
                "protocols"
            ]["documents"],
            "protocol_scope_effects": matrix_row[
                "protocols"
            ]["scope_effects"],
            "mli_effects": matrix_row["mli_effects"],
            "review_questions": [],
            "reviewer_findings": {
                "treaty_rates_confirmed": None,
                "rate_categories_confirmed": None,
                "special_exemptions_confirmed": None,
                "beneficial_owner_requirement_confirmed": None,
                "protocol_effect_confirmed": None,
                "mli_effect_confirmed": None,
                "domestic_rate_confirmed": None,
                "eu_relief_conditions_confirmed": None,
                "effective_dates_confirmed": None,
                "supporting_source_ids": [],
                "notes": None,
            },
            "proposed_rule_snapshot": None,
            "review_outcome": None,
            "status": "awaiting_primary_review",
        }

        if income_type == "dividend":
            scope["review_questions"] = [
                (
                    "Does the 5% rate require direct or direct/indirect "
                    "ownership of at least 25%?"
                ),
                (
                    "Is the 15% rate the residual rate for all other "
                    "beneficial owners?"
                ),
                (
                    "Does the protocol leave Article 10 unchanged?"
                ),
                (
                    "Are the Czech PSD conditions correctly represented, "
                    "including the 12-month holding-period rule?"
                ),
            ]

        elif income_type == "interest":
            scope["review_questions"] = [
                (
                    "Is 10% the general treaty ceiling subject to "
                    "beneficial ownership?"
                ),
                (
                    "Which Article 11(3) categories qualify for a 0% "
                    "source-state exemption?"
                ),
                (
                    "Are bank loans, deposits, trade credits, export "
                    "finance and government payments represented correctly?"
                ),
                (
                    "Are the Czech IRD conditions and section 38nb "
                    "requirement correctly represented?"
                ),
            ]

        elif income_type == "royalty":
            scope["review_questions"] = [
                (
                    "Which royalty categories are subject to the 5% rate?"
                ),
                (
                    "Which royalty categories are subject to the 10% rate?"
                ),
                (
                    "Does the treaty definition include software, know-how, "
                    "industrial equipment or copyright separately?"
                ),
                (
                    "Does the protocol leave Article 12 unchanged?"
                ),
                (
                    "Are the Czech IRD conditions and section 38nb "
                    "requirement correctly represented?"
                ),
            ]

        scopes.append(scope)

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-belgium-worksheet-2026-08-05.1"
        ),
        "country": "BE",
        "country_name": "Belgie",
        "policy": {
            "candidate_data_only": True,
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "fail_closed": True,
        },
        "summary": {
            "scopes": 3,
            "completed_primary_reviews": 0,
            "approved_scopes": 0,
        },
        "scopes": scopes,
    }

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
    payload = build_worksheet()

    print("Belgium legal review worksheet created.")
    print("Scopes:", payload["summary"]["scopes"])
    print(
        "Completed primary reviews:",
        payload["summary"]["completed_primary_reviews"],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
