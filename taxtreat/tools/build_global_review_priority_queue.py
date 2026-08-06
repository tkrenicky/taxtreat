from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

WORKSTREAMS_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams.json"
)

OUTPUT_PATH = (
    GLOBAL_DIR
    / "global_review_priority_queue.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_priority_queue_summary.json"
)


PRIMARY_PRIORITY = {
    "treaty_status_instrument_review": 1,
    "pilot_structure_reconciliation": 2,
    "protocol_effect_review": 3,
    "mli_ppt_and_effective_date_review": 4,
    "base_treaty_semantic_review": 5,
}

INCOME_PRIORITY = {
    "dividend": 1,
    "interest": 2,
    "royalty": 3,
}


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _priority_tier(
    primary_workstream: str,
) -> str:
    rank = PRIMARY_PRIORITY[
        primary_workstream
    ]

    if rank == 1:
        return "P0"
    if rank == 2:
        return "P1"
    if rank == 3:
        return "P2"
    if rank == 4:
        return "P3"

    return "P4"


def _review_complexity(
    row: dict[str, Any],
) -> int:
    score = len(row["review_workstreams"])

    if row["has_status_instrument"]:
        score += 5

    if row["pilot_structure_exception"]:
        score += 4

    if row["has_protocol_effect"]:
        score += 3

    if row["has_mli_effect"]:
        score += 2

    if row["has_eu_or_domestic_relief"]:
        score += 1

    return score


def _queue_sort_key(
    row: dict[str, Any],
) -> tuple[Any, ...]:
    return (
        PRIMARY_PRIORITY[
            row["primary_review_workstream"]
        ],
        -row["review_complexity_score"],
        row["recipient_country"],
        INCOME_PRIORITY[row["income_type"]],
        row["packet_id"],
    )


def build_priority_queue() -> dict[str, Any]:
    payload = json.loads(
        WORKSTREAMS_PATH.read_text(
            encoding="utf-8"
        )
    )

    rows: list[dict[str, Any]] = []

    for source in payload["scopes"]:
        primary = source[
            "primary_review_workstream"
        ]

        if primary not in PRIMARY_PRIORITY:
            raise ValueError(
                f"Unknown primary workstream: "
                f"{primary}"
            )

        if source["income_type"] not in (
            INCOME_PRIORITY
        ):
            raise ValueError(
                f"Unknown income type: "
                f"{source['income_type']}"
            )

        row = {
            "packet_id": source["packet_id"],
            "recipient_country": (
                source["recipient_country"]
            ),
            "recipient_country_name": (
                source["recipient_country_name"]
            ),
            "income_type": (
                source["income_type"]
            ),
            "primary_review_workstream": (
                primary
            ),
            "review_workstreams": (
                source["review_workstreams"]
            ),
            "priority_tier": (
                _priority_tier(primary)
            ),
            "review_complexity_score": (
                _review_complexity(source)
            ),
            "has_status_instrument": (
                source[
                    "has_status_instrument"
                ]
            ),
            "pilot_structure_exception": (
                source[
                    "pilot_structure_exception"
                ]
            ),
            "has_protocol_effect": (
                source[
                    "has_protocol_effect"
                ]
            ),
            "has_mli_effect": (
                source["has_mli_effect"]
            ),
            "has_eu_or_domestic_relief": (
                source[
                    "has_eu_or_domestic_relief"
                ]
            ),
            "status": (
                "queued_for_primary_review"
            ),
            "approval_eligible": False,
            "promotable_to_active_rules": False,
            "source_workstream_sha256": (
                source["workstream_sha256"]
            ),
        }

        row["queue_item_sha256"] = (
            _sha256_json(row)
        )

        rows.append(row)

    if len(rows) != 300:
        raise ValueError(
            f"Expected 300 queue items, "
            f"found {len(rows)}."
        )

    rows.sort(key=_queue_sort_key)

    for index, row in enumerate(
        rows,
        start=1,
    ):
        row["queue_position"] = index

    if any(
        row["approval_eligible"]
        or row["promotable_to_active_rules"]
        for row in rows
    ):
        raise ValueError(
            "Priority queue must remain "
            "fail-closed."
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-review-priority-queue-"
            "2026-08-06.1"
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "policy": {
            "fail_closed": True,
            "queue_order_is_not_legal_approval":
                True,
            "priority_tiers": {
                "P0": (
                    "treaty status instruments"
                ),
                "P1": (
                    "pilot structure "
                    "reconciliation"
                ),
                "P2": "protocol effects",
                "P3": (
                    "MLI and effective dates"
                ),
                "P4": (
                    "base treaty semantics"
                ),
            },
        },
        "queue": rows,
    }


def build_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    rows = payload["queue"]

    return {
        "schema_version": 1,
        "dataset_release": (
            payload["dataset_release"]
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "priority_tier_counts": dict(
            sorted(
                Counter(
                    row["priority_tier"]
                    for row in rows
                ).items()
            )
        ),
        "primary_workstream_counts": dict(
            sorted(
                Counter(
                    row[
                        "primary_review_workstream"
                    ]
                    for row in rows
                ).items()
            )
        ),
        "income_type_counts": dict(
            sorted(
                Counter(
                    row["income_type"]
                    for row in rows
                ).items()
            )
        ),
        "highest_priority_packet_ids": [
            row["packet_id"]
            for row in rows[:12]
        ],
        "approval_eligible_scopes": 0,
        "promotable_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_priority_queue()
    summary = build_summary(payload)

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Scopes:", payload["scope_count"])
    print(
        "Priority tiers:",
        summary["priority_tier_counts"],
    )
    print(
        "First 12:",
        summary[
            "highest_priority_packet_ids"
        ],
    )


if __name__ == "__main__":
    main()
