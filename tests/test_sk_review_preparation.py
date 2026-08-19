from __future__ import annotations

import json
from pathlib import Path

from taxtreat.tools.build_sk_review_preparation import (
    SAMPLE_PACKET_IDS,
    build_first_human_review_sample,
    build_machine_preparation,
    build_summary,
)


ROOT = Path(__file__).resolve().parents[1]


def test_sk_machine_preparation_covers_all_225_scopes_fail_closed():
    payload = build_machine_preparation()
    summary = build_summary(payload)

    assert payload["source_country"] == "SK"
    assert payload["country_count"] == 75
    assert payload["scope_count"] == 225
    assert len(payload["scopes"]) == 225
    assert len({row["packet_id"] for row in payload["scopes"]}) == 225

    assert summary["machine_prepared_scopes"] == 225
    assert summary["review_ready_scopes"] == 0
    assert summary["human_reviewed_scopes"] == 0
    assert summary["production_released_scopes"] == 0

    assert summary["mli_relationship_count"] == 46
    assert summary["mli_scope_count"] == 138

    assert summary["risk_country_counts"] == {
        "ELEVATED": 8,
        "STANDARD": 67,
    }
    assert summary["risk_scope_counts"] == {
        "ELEVATED": 24,
        "STANDARD": 201,
    }

    assert all(
        row["machine_preparation_status"]
        == "inventory_ready_treaty_text_pending"
        for row in payload["scopes"]
    )
    assert all(not row["review_ready"] for row in payload["scopes"])
    assert all(not row["approval_eligible"] for row in payload["scopes"])
    assert all(
        not row["promotable_to_active_rules"]
        for row in payload["scopes"]
    )
    assert all(
        row["runtime_status"] == "not_released"
        for row in payload["scopes"]
    )


def test_mli_only_relationships_remain_standard():
    payload = build_machine_preparation()
    by_packet = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    austria = by_packet["SK-AT-dividend"]
    australia = by_packet["SK-AU-royalty"]

    assert austria["has_mli_effect"] is True
    assert austria["risk_tier"] == "STANDARD"
    assert austria["risk_reasons"] == []

    assert australia["has_mli_effect"] is True
    assert australia["risk_tier"] == "STANDARD"
    assert australia["risk_reasons"] == []


def test_country_specific_instrument_complexity_is_elevated():
    payload = build_machine_preparation()
    by_packet = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    assert by_packet["SK-NL-dividend"]["risk_tier"] == "ELEVATED"
    assert "protocol_overlay" in by_packet["SK-NL-dividend"]["risk_reasons"]

    assert by_packet["SK-GB-interest"]["risk_tier"] == "ELEVATED"
    assert "correction_notice" in by_packet["SK-GB-interest"]["risk_reasons"]
    assert "territorial_scope_note" in by_packet["SK-GB-interest"]["risk_reasons"]

    assert by_packet["SK-CH-royalty"]["risk_tier"] == "ELEVATED"
    assert "prevailing_text_feature" in by_packet["SK-CH-royalty"]["risk_reasons"]

    assert by_packet["SK-TW-royalty"]["risk_tier"] == "ELEVATED"
    assert "non_standard_publication" in by_packet["SK-TW-royalty"]["risk_reasons"]


def test_first_human_review_sample_is_deterministic_4_standard_2_elevated():
    payload = build_machine_preparation()
    sample = build_first_human_review_sample(payload)

    rows = sample["sample"]

    assert tuple(row["packet_id"] for row in rows) == SAMPLE_PACKET_IDS
    assert sum(row["risk_tier"] == "STANDARD" for row in rows) == 4
    assert sum(row["risk_tier"] == "ELEVATED" for row in rows) == 2
    assert sample["review_ready"] is False
    assert "Primary treaty text" in sample["review_blocker"]


def test_treaty_instrument_inventory_matches_official_counts():
    path = (
        ROOT
        / "data"
        / "legal_reviews"
        / "sk_outbound"
        / "treaty_instrument_inventory.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source_country"] == "SK"
    assert len(payload["relationships"]) == 75
    assert sum(
        row["mli_listed_modified"]
        for row in payload["relationships"]
    ) == 46
    assert payload["policy"]["mli_listing_alone_is_not_elevated"] is True
    assert payload["policy"]["runtime_release"] is False
