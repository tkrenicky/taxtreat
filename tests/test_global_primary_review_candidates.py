from __future__ import annotations

import json
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
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _summary():
    return json.loads(
        SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_all_remaining_scopes_are_present():
    payload = _data()

    assert payload["scope_count"] == 294
    assert len(payload["scopes"]) == 294
    assert payload["country_count"] == 98


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


def test_every_scope_remains_fail_closed():
    payload = _data()

    assert payload["fail_closed"] is True
    assert (
        payload[
            "promotable_to_active_rules"
        ]
        is False
    )

    assert all(
        row["fail_closed"] is True
        and row[
            "promotable_to_active_rules"
        ] is False
        for row in payload["scopes"]
    )


def test_summary_matches_data():
    payload = _data()
    summary = _summary()

    assert (
        summary["scope_count"]
        == payload["scope_count"]
    )
    assert (
        sum(
            summary[
                "resolution_class_counts"
            ].values()
        )
        == 294
    )


def test_packet_ids_are_unique():
    packet_ids = [
        row["packet_id"]
        for row in _data()["scopes"]
    ]

    assert len(packet_ids) == len(
        set(packet_ids)
    )


def test_classification_has_expected_distribution():
    counts = _summary()[
        "resolution_class_counts"
    ]

    assert counts == {
        "candidate_ready_for_owner_review": 189,
        "conditional_mapping_required": 98,
        "manual_exception_review": 7,
    }


def test_only_seven_scopes_need_source_exception_review():
    scopes = _data()["scopes"]

    exceptions = [
        row
        for row in scopes
        if row["resolution_class"]
        == "manual_exception_review"
    ]

    assert len(exceptions) == 7

    assert all(
        row["hard_unresolved_codes"]
        for row in exceptions
    )


def test_process_markers_do_not_force_manual_review():
    scopes = _data()["scopes"]

    assert any(
        row["process_review_codes"]
        and row["resolution_class"]
        == "candidate_ready_for_owner_review"
        for row in scopes
    )
