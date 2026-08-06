from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.tools.build_global_review_priority_queue import (
    PRIMARY_PRIORITY,
    build_priority_queue,
    build_summary,
)


ROOT = Path(__file__).parents[1]

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

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_priority_queue_summary.json"
)


def _queue():
    return json.loads(
        QUEUE_PATH.read_text(
            encoding="utf-8"
        )
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_all_scopes_are_queued():
    payload = _queue()

    assert payload["scope_count"] == 300
    assert payload["country_count"] == 100
    assert len(payload["queue"]) == 300

    assert [
        row["queue_position"]
        for row in payload["queue"]
    ] == list(range(1, 301))


def test_queue_remains_fail_closed():
    for row in _queue()["queue"]:
        assert row["status"] == (
            "queued_for_primary_review"
        )
        assert row[
            "approval_eligible"
        ] is False
        assert row[
            "promotable_to_active_rules"
        ] is False


def test_priority_order_is_monotonic():
    ranks = [
        PRIMARY_PRIORITY[
            row[
                "primary_review_workstream"
            ]
        ]
        for row in _queue()["queue"]
    ]

    assert ranks == sorted(ranks)


def test_status_instruments_are_first():
    first_six = _queue()["queue"][:6]

    assert {
        row["recipient_country"]
        for row in first_six
    } == {"BY", "RU"}

    assert all(
        row["priority_tier"] == "P0"
        for row in first_six
    )


def test_pilot_scopes_follow_status_cases():
    pilot_rows = [
        row
        for row in _queue()["queue"]
        if row[
            "pilot_structure_exception"
        ]
    ]

    assert len(pilot_rows) == 6
    assert all(
        row["priority_tier"] == "P1"
        for row in pilot_rows
    )
    assert {
        row["recipient_country"]
        for row in pilot_rows
    } == {"AT", "CH"}


def test_priority_tier_counts():
    summary = _summary()

    assert summary[
        "priority_tier_counts"
    ] == {
        "P0": 6,
        "P1": 6,
        "P2": 27,
        "P3": 183,
        "P4": 78,
    }


def test_income_types_are_balanced():
    assert _summary()[
        "income_type_counts"
    ] == {
        "dividend": 100,
        "interest": 100,
        "royalty": 100,
    }


def test_summary_matches_payload():
    payload = _queue()

    assert build_summary(
        payload
    ) == _summary()


def test_generation_is_deterministic():
    assert build_priority_queue() == _queue()


def test_hashes_are_stable():
    for row in _queue()["queue"]:
        expected = row[
            "queue_item_sha256"
        ]

        source = {
            key: value
            for key, value in row.items()
            if key not in {
                "queue_item_sha256",
                "queue_position",
            }
        }

        actual = hashlib.sha256(
            json.dumps(
                source,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        assert actual == expected
