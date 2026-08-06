from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]

DATA_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "global_primary_review_candidates.json"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "global_primary_review_candidates_summary.json"
)


def _data():
    return json.loads(
        DATA_PATH.read_text(encoding="utf-8")
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(encoding="utf-8")
    )


def test_all_remaining_scopes_are_present():
    payload = _data()

    assert payload["scope_count"] == 294
    assert len(payload["scopes"]) == 294
    assert payload["country_count"] == 98


def test_packet_ids_are_unique():
    packet_ids = [
        row["packet_id"]
        for row in _data()["scopes"]
    ]

    assert len(packet_ids) == len(set(packet_ids))


def test_russia_and_belarus_are_excluded():
    countries = {
        row["recipient_country"]
        for row in _data()["scopes"]
    }

    assert "RU" not in countries
    assert "BY" not in countries


def test_every_scope_is_classified():
    allowed = {
        "candidate_ready_for_owner_review",
        "conditional_mapping_required",
        "manual_exception_review",
        "manual_status_review",
    }

    assert all(
        row["resolution_class"] in allowed
        for row in _data()["scopes"]
    )


def test_summary_distribution_matches_data():
    payload = _data()
    summary = _summary()

    actual = Counter(
        row["resolution_class"]
        for row in payload["scopes"]
    )

    assert (
        summary["resolution_class_counts"]
        == dict(sorted(actual.items()))
    )
    assert sum(actual.values()) == 294


def test_single_rate_candidates_have_rate():
    rows = [
        row
        for row in _data()["scopes"]
        if row["resolution_class"]
        == "candidate_ready_for_owner_review"
    ]

    assert rows
    assert all(
        row["resolved_rate_candidate"] is not None
        for row in rows
    )


def test_conditional_cases_have_multiple_rate_marker():
    rows = [
        row
        for row in _data()["scopes"]
        if row["resolution_class"]
        == "conditional_mapping_required"
    ]

    assert all(
        "multiple_rate_conditions"
        in row["conditional_codes"]
        for row in rows
    )


def test_manual_exceptions_have_hard_reason():
    rows = [
        row
        for row in _data()["scopes"]
        if row["resolution_class"]
        in {
            "manual_exception_review",
            "manual_status_review",
        }
    ]

    assert all(
        row["hard_unresolved_codes"]
        for row in rows
    )


def test_process_markers_alone_do_not_force_exception():
    rows = _data()["scopes"]

    assert any(
        row["process_review_codes"]
        and row["resolution_class"]
        in {
            "candidate_ready_for_owner_review",
            "conditional_mapping_required",
        }
        for row in rows
    )


def test_every_scope_remains_fail_closed():
    payload = _data()

    assert payload["fail_closed"] is True
    assert payload["promotable_to_active_rules"] is False

    assert all(
        row["fail_closed"] is True
        and row["promotable_to_active_rules"] is False
        for row in payload["scopes"]
    )
