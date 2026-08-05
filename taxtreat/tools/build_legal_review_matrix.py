from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

BATCH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_priority_eu.json"
)

BASE = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "remaining_294_base_candidates.json"
)

PROTOCOLS = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "protocol_effect_candidates.json"
)

MLI = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "mli_wht_effects.json"
)

DOMESTIC = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "cz_domestic_eu_candidates.json"
)

BLOCKERS = (
    ROOT
    / "data"
    / "legal_consolidation"
    / "blocker_resolutions.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


def build_matrix() -> dict[str, Any]:
    batch = read_json(BATCH)
    base = read_json(BASE)
    protocols = read_json(PROTOCOLS)
    mli = read_json(MLI)
    domestic = read_json(DOMESTIC)
    blockers = read_json(BLOCKERS)

    base_index = {
        (
            item["recipient_country"],
            item["income_type"],
        ): item
        for item in base["scopes"]
    }

    domestic_index = {
        (
            item["recipient_country"],
            item["income_type"],
        ): item
        for item in domestic["scopes"]
    }

    protocol_documents = {}

    for item in protocols.get("documents", []):
        protocol_documents.setdefault(
            item["recipient_country"],
            [],
        ).append(item)

    protocol_scopes = {}

    for item in protocols.get("scopes", []):
        key = (
            item.get("recipient_country"),
            item.get("income_type"),
        )
        protocol_scopes.setdefault(key, []).append(item)

    mli_index = {}

    for item in mli.get("effects", []):
        country = item["recipient_country"]

        for income_type in item.get(
            "applies_to_income_types",
            [],
        ):
            mli_index.setdefault(
                (country, income_type),
                [],
            ).append(item)

    blocker_index = {}

    for item in blockers.get(
        "base_treaty_resolutions",
        [],
    ):
        blocker_index[
            (
                item["recipient_country"],
                item["income_type"],
            )
        ] = item

    rows = []

    for packet in batch["packets"]:
        key = (
            packet["recipient_country"],
            packet["income_type"],
        )

        base_item = base_index[key]
        domestic_item = domestic_index[key]

        row = {
            "packet_id": packet["packet_id"],
            "recipient_country": packet["recipient_country"],
            "recipient_country_name": packet[
                "recipient_country_name"
            ],
            "income_type": packet["income_type"],
            "base_treaty": {
                "publication": base_item.get(
                    "base_treaty_publication"
                ),
                "source_id": base_item.get(
                    "base_treaty_source_id"
                ),
                "article_number": base_item.get(
                    "article_number"
                ),
                "article_title": base_item.get(
                    "article_title"
                ),
                "rate_candidates": base_item.get(
                    "rate_candidates",
                    [],
                ),
                "discarded_rate_candidates": base_item.get(
                    "discarded_rate_candidates",
                    [],
                ),
                "source_state_taxation_candidate": (
                    base_item.get(
                        "source_state_taxation_candidate"
                    )
                ),
                "treaty_rate_cap_status": base_item.get(
                    "treaty_rate_cap_status"
                ),
                "candidate_status": base_item.get(
                    "candidate_status"
                ),
                "verification_status": base_item.get(
                    "verification_status"
                ),
                "risk_flags": base_item.get(
                    "risk_flags",
                    [],
                ),
                "consolidation_blockers": base_item.get(
                    "consolidation_blockers",
                    [],
                ),
                "article_text_sha256": base_item.get(
                    "article_text_sha256"
                ),
            },
            "protocols": {
                "documents": protocol_documents.get(
                    packet["recipient_country"],
                    [],
                ),
                "scope_effects": protocol_scopes.get(
                    key,
                    [],
                ),
            },
            "mli_effects": mli_index.get(key, []),
            "domestic_and_eu": {
                "domestic_rate_candidate": (
                    domestic_item.get(
                        "domestic_rate_candidate"
                    )
                ),
                "relief_candidate": domestic_item.get(
                    "relief_candidate"
                ),
                "relief_candidate_status": (
                    domestic_item.get(
                        "relief_candidate_status"
                    )
                ),
                "relief_eligible_by_jurisdiction": (
                    domestic_item.get(
                        "relief_eligible_by_jurisdiction"
                    )
                ),
                "candidate_status": domestic_item.get(
                    "candidate_status"
                ),
                "verification_status": domestic_item.get(
                    "verification_status"
                ),
                "consolidation_blockers": (
                    domestic_item.get(
                        "consolidation_blockers",
                        [],
                    )
                ),
            },
            "blocker_resolution": blocker_index.get(key),
            "review": {
                "reviewer_id": None,
                "reviewed_at": None,
                "domestic_rate_confirmed": None,
                "treaty_rate_candidates_confirmed": None,
                "protocol_effects_confirmed": None,
                "mli_effects_confirmed": None,
                "eu_relief_confirmed": None,
                "effective_date_confirmed": None,
                "beneficial_owner_requirement_confirmed": None,
                "anti_abuse_review_completed": None,
                "supporting_source_ids": [],
                "reviewer_notes": None,
                "proposed_rule_snapshot": None,
                "review_outcome": None,
            },
            "status": "awaiting_primary_review",
            "approval_eligible": False,
            "promotable_to_active_rules": False,
        }

        row["review_row_sha256"] = stable_hash(row)
        rows.append(row)

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "legal-review-batch-01-matrix-2026-08-05.1"
        ),
        "source_batch_release": batch["dataset_release"],
        "source_dataset_releases": {
            "base_treaty": base["dataset_release"],
            "protocols": protocols["dataset_release"],
            "mli": mli["dataset_release"],
            "domestic_eu": domestic["dataset_release"],
            "blocker_resolutions": blockers[
                "dataset_release"
            ],
        },
        "policy": {
            "candidate_data_only": True,
            "primary_legal_review_required": True,
            "independent_approval_required": True,
            "fail_closed": True,
            "no_automatic_legal_conclusions": True,
        },
        "summary": {
            "rows": len(rows),
            "countries": len(
                {
                    row["recipient_country"]
                    for row in rows
                }
            ),
            "awaiting_primary_review": len(rows),
            "approved": 0,
        },
        "rows": rows,
    }

    if len(rows) != 30:
        raise ValueError(
            f"Expected 30 review rows, found {len(rows)}."
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
    payload = build_matrix()

    print("Legal review matrix created.")
    print("Rows:", payload["summary"]["rows"])
    print("Countries:", payload["summary"]["countries"])
    print(
        "Awaiting primary review:",
        payload["summary"][
            "awaiting_primary_review"
        ],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
