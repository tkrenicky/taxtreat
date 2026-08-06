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

QUEUE_PATH = (
    GLOBAL_DIR
    / "global_review_priority_queue.json"
)

OUTPUT_PATH = (
    GLOBAL_DIR
    / "global_review_batches.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_batches_summary.json"
)

MAX_COUNTRIES_PER_BATCH = 5
MAX_SCOPES_PER_BATCH = 15


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _country_groups(
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str],
        list[dict[str, Any]],
    ] = {}

    for row in queue:
        key = (
            row["priority_tier"],
            row["recipient_country"],
        )
        grouped.setdefault(key, []).append(row)

    groups = []

    for (
        priority_tier,
        country,
    ), rows in grouped.items():
        rows.sort(
            key=lambda row: row["queue_position"]
        )

        groups.append({
            "priority_tier": priority_tier,
            "recipient_country": country,
            "recipient_country_name": rows[0][
                "recipient_country_name"
            ],
            "first_queue_position": rows[0][
                "queue_position"
            ],
            "scope_count": len(rows),
            "queue_items": rows,
        })

    groups.sort(
        key=lambda group: (
            group["first_queue_position"],
            group["recipient_country"],
        )
    )

    return groups


def build_batches() -> dict[str, Any]:
    queue_payload = json.loads(
        QUEUE_PATH.read_text(
            encoding="utf-8"
        )
    )

    queue = queue_payload["queue"]

    if len(queue) != 300:
        raise ValueError(
            f"Expected 300 queue items, "
            f"found {len(queue)}."
        )

    country_groups = _country_groups(queue)

    if len(country_groups) != 100:
        raise ValueError(
            f"Expected 100 country groups, "
            f"found {len(country_groups)}."
        )

    batches: list[dict[str, Any]] = []
    current_groups: list[dict[str, Any]] = []
    current_tier: str | None = None

    def flush() -> None:
        nonlocal current_groups
        nonlocal current_tier

        if not current_groups:
            return

        queue_items = [
            item
            for group in current_groups
            for item in group["queue_items"]
        ]

        batch_number = len(batches) + 1

        batch = {
            "batch_id": (
                f"GLOBAL-CZ-OUTBOUND-"
                f"BATCH-{batch_number:02d}"
            ),
            "batch_number": batch_number,
            "priority_tier": current_tier,
            "country_count": len(
                current_groups
            ),
            "scope_count": len(queue_items),
            "countries": [
                group["recipient_country"]
                for group in current_groups
            ],
            "country_names": [
                group[
                    "recipient_country_name"
                ]
                for group in current_groups
            ],
            "first_queue_position": min(
                row["queue_position"]
                for row in queue_items
            ),
            "last_queue_position": max(
                row["queue_position"]
                for row in queue_items
            ),
            "packet_ids": [
                row["packet_id"]
                for row in queue_items
            ],
            "primary_workstreams": sorted({
                row[
                    "primary_review_workstream"
                ]
                for row in queue_items
            }),
            "status": (
                "awaiting_primary_legal_review"
            ),
            "approval_eligible": False,
            "promotable_to_active_rules": False,
        }

        batch["batch_sha256"] = (
            _sha256_json(batch)
        )

        batches.append(batch)
        current_groups = []
        current_tier = None

    for group in country_groups:
        tier_changed = (
            current_tier is not None
            and group["priority_tier"]
            != current_tier
        )

        country_limit_reached = (
            len(current_groups)
            >= MAX_COUNTRIES_PER_BATCH
        )

        scope_count = sum(
            item["scope_count"]
            for item in current_groups
        )

        scope_limit_exceeded = (
            scope_count
            + group["scope_count"]
            > MAX_SCOPES_PER_BATCH
        )

        if (
            tier_changed
            or country_limit_reached
            or scope_limit_exceeded
        ):
            flush()

        if current_tier is None:
            current_tier = (
                group["priority_tier"]
            )

        current_groups.append(group)

    flush()

    packet_ids = [
        packet_id
        for batch in batches
        for packet_id in batch[
            "packet_ids"
        ]
    ]

    if len(packet_ids) != 300:
        raise ValueError(
            "Not all queue items were assigned."
        )

    if len(set(packet_ids)) != 300:
        raise ValueError(
            "Duplicate queue item assignment."
        )

    if any(
        batch["country_count"]
        > MAX_COUNTRIES_PER_BATCH
        or batch["scope_count"]
        > MAX_SCOPES_PER_BATCH
        for batch in batches
    ):
        raise ValueError(
            "Batch capacity exceeded."
        )

    if any(
        batch["approval_eligible"]
        or batch[
            "promotable_to_active_rules"
        ]
        for batch in batches
    ):
        raise ValueError(
            "Review batches must remain "
            "fail-closed."
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-review-batches-"
            "2026-08-06.1"
        ),
        "scope_count": 300,
        "country_count": 100,
        "batch_count": len(batches),
        "policy": {
            "fail_closed": True,
            "maximum_countries_per_batch":
                MAX_COUNTRIES_PER_BATCH,
            "maximum_scopes_per_batch":
                MAX_SCOPES_PER_BATCH,
            "country_may_not_be_split":
                True,
            "priority_tiers_may_not_be_mixed":
                True,
            "batch_assignment_is_not_legal_approval":
                True,
        },
        "batches": batches,
    }


def build_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    batches = payload["batches"]

    return {
        "schema_version": 1,
        "dataset_release": (
            payload["dataset_release"]
        ),
        "batch_count": len(batches),
        "scope_count": sum(
            batch["scope_count"]
            for batch in batches
        ),
        "country_count": sum(
            batch["country_count"]
            for batch in batches
        ),
        "priority_tier_batch_counts": dict(
            sorted(
                Counter(
                    batch["priority_tier"]
                    for batch in batches
                ).items()
            )
        ),
        "priority_tier_scope_counts": dict(
            sorted(
                Counter({
                    tier: sum(
                        batch["scope_count"]
                        for batch in batches
                        if batch[
                            "priority_tier"
                        ] == tier
                    )
                    for tier in {
                        batch["priority_tier"]
                        for batch in batches
                    }
                }).items()
            )
        ),
        "first_batch": {
            "batch_id": batches[0][
                "batch_id"
            ],
            "priority_tier": batches[0][
                "priority_tier"
            ],
            "countries": batches[0][
                "countries"
            ],
            "scope_count": batches[0][
                "scope_count"
            ],
        },
        "approval_eligible_scopes": 0,
        "promotable_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_batches()
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

    print("Batches:", payload["batch_count"])
    print("Scopes:", payload["scope_count"])
    print("Countries:", payload["country_count"])
    print(
        "Tier batches:",
        summary[
            "priority_tier_batch_counts"
        ],
    )
    print(
        "First batch:",
        summary["first_batch"],
    )


if __name__ == "__main__":
    main()
