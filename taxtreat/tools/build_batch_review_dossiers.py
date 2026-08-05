from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

MATRIX = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)

BASE = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_base_candidates.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_country_dossiers.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(
        r"(?=\n?\s*\d+\.\s+)",
        text.strip(),
    )

    return [
        normalize_text(part)
        for part in parts
        if part.strip()
    ]


def build_dossiers() -> dict[str, Any]:
    matrix = read_json(MATRIX)
    base = read_json(BASE)

    base_index = {
        (
            item["recipient_country"],
            item["income_type"],
        ): item
        for item in base["scopes"]
    }

    countries: dict[str, dict[str, Any]] = {}

    for row in matrix["rows"]:
        country = row["recipient_country"]
        income_type = row["income_type"]
        base_row = base_index[(country, income_type)]

        dossier = countries.setdefault(
            country,
            {
                "recipient_country": country,
                "recipient_country_name": row[
                    "recipient_country_name"
                ],
                "status": "awaiting_primary_review",
                "review_completion_percent": 0,
                "scopes": [],
            },
        )

        dossier["scopes"].append(
            {
                "packet_id": row["packet_id"],
                "income_type": income_type,
                "article_number": base_row[
                    "article_number"
                ],
                "article_title": base_row[
                    "article_title"
                ],
                "treaty_publication": base_row[
                    "base_treaty_publication"
                ],
                "treaty_source_id": base_row[
                    "base_treaty_source_id"
                ],
                "article_text_sha256": base_row[
                    "article_text_sha256"
                ],
                "article_paragraphs": split_paragraphs(
                    base_row["article_text"]
                ),
                "rate_candidates": base_row.get(
                    "rate_candidates",
                    [],
                ),
                "discarded_rate_candidates": base_row.get(
                    "discarded_rate_candidates",
                    [],
                ),
                "protocol_documents": row[
                    "protocols"
                ]["documents"],
                "protocol_scope_effects": row[
                    "protocols"
                ]["scope_effects"],
                "mli_effects": row["mli_effects"],
                "domestic_rate_candidate": row[
                    "domestic_and_eu"
                ]["domestic_rate_candidate"],
                "eu_relief_candidate": row[
                    "domestic_and_eu"
                ]["relief_candidate"],
                "review": {
                    "base_treaty_confirmed": None,
                    "rates_confirmed": None,
                    "rate_categories_confirmed": None,
                    "special_exemptions_confirmed": None,
                    "protocol_effects_confirmed": None,
                    "mli_effects_confirmed": None,
                    "domestic_rate_confirmed": None,
                    "eu_relief_confirmed": None,
                    "effective_dates_confirmed": None,
                    "anti_abuse_review_completed": None,
                    "reviewer_id": None,
                    "reviewed_at": None,
                    "supporting_source_ids": [],
                    "notes": None,
                    "outcome": None,
                },
                "status": "awaiting_primary_review",
                "approval_eligible": False,
            }
        )

    ordered_countries = [
        countries[code]
        for code in sorted(countries)
    ]

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-country-dossiers-"
            "2026-08-05.1"
        ),
        "policy": {
            "candidate_data_only": True,
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "fail_closed": True,
            "automatic_approval_prohibited": True,
        },
        "summary": {
            "countries": len(ordered_countries),
            "scopes": sum(
                len(country["scopes"])
                for country in ordered_countries
            ),
            "completed_primary_reviews": 0,
            "approved_scopes": 0,
        },
        "countries": ordered_countries,
    }

    if payload["summary"]["countries"] != 10:
        raise ValueError("Expected 10 countries.")

    if payload["summary"]["scopes"] != 30:
        raise ValueError("Expected 30 scopes.")

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
    payload = build_dossiers()

    print("Batch country dossiers created.")
    print("Countries:", payload["summary"]["countries"])
    print("Scopes:", payload["summary"]["scopes"])
    print(
        "Completed primary reviews:",
        payload["summary"]["completed_primary_reviews"],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
