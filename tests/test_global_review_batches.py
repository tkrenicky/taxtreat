from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxtreat.tools.build_global_review_batches import (
    MAX_COUNTRIES_PER_BATCH,
    MAX_SCOPES_PER_BATCH,
    build_batches,
    build_summary,
)


ROOT = Path(__file__).parents[1]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

BATCHES_PATH = (
    GLOBAL_DIR
    / "global_review_batches.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_batches_summary.json"
)


def _payload():
    return json.loads(
        BATCHES_PATH.read_text(
            encoding="utf-8"
        )
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_all_scopes_are_assigned_once():
    payload = _payload()

    packet_ids = [
        packet_id
        for batch in payload["batches"]
        for packet_id in batch[
            "packet_ids"
        ]
    ]

    assert payload["scope_count"] == 300
    assert len(packet_ids) == 300
    assert len(set(packet_ids)) == 300


def test_all_countries_are_assigned_once():
    countries = [
        country
        for batch in _payload()["batches"]
        for country in batch["countries"]
    ]

    assert len(countries) == 100
    assert len(set(countries)) == 100


def test_batch_capacity_is_respected():
    for batch in _payload()["batches"]:
        assert (
            batch["country_count"]
            <= MAX_COUNTRIES_PER_BATCH
        )
        assert (
            batch["scope_count"]
            <= MAX_SCOPES_PER_BATCH
        )


def test_priority_tiers_are_not_mixed():
    for batch in _payload()["batches"]:
        assert batch["priority_tier"] in {
            "P0",
            "P1",
            "P2",
            "P3",
            "P4",
        }


def test_first_batch_contains_status_cases():
    first = _payload()["batches"][0]

    assert first["priority_tier"] == "P0"
    assert set(first["countries"]) == {
        "BY",
        "RU",
    }
    assert first["scope_count"] == 6


def test_second_batch_contains_pilots():
    second = _payload()["batches"][1]

    assert second["priority_tier"] == "P1"
    assert set(second["countries"]) == {
        "AT",
        "CH",
    }
    assert second["scope_count"] == 6


def test_batches_remain_fail_closed():
    for batch in _payload()["batches"]:
        assert batch["status"] == (
            "awaiting_primary_legal_review"
        )
        assert (
            batch["approval_eligible"]
            is False
        )
        assert (
            batch[
                "promotable_to_active_rules"
            ]
            is False
        )


def test_queue_positions_are_contiguous():
    previous_last = 0

    for batch in _payload()["batches"]:
        assert (
            batch["first_queue_position"]
            == previous_last + 1
        )

        previous_last = batch[
            "last_queue_position"
        ]

    assert previous_last == 300


def test_hashes_are_stable():
    for batch in _payload()["batches"]:
        expected = batch["batch_sha256"]

        source = {
            key: value
            for key, value in batch.items()
            if key != "batch_sha256"
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


def test_summary_matches_payload():
    payload = _payload()

    assert build_summary(
        payload
    ) == _summary()


def test_generation_is_deterministic():
    assert build_batches() == _payload()
