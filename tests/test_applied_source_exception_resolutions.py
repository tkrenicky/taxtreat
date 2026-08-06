import json
from pathlib import Path

ROOT = (
    Path(__file__).parents[1]
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)


def load(name):
    return json.loads(
        (ROOT / name).read_text(encoding="utf-8")
    )


def test_all_exception_resolutions_are_applied():
    payload = load(
        "global_primary_review_candidates_resolved.json"
    )

    rows = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    expected = {
        "CZ-AT-DIV-LEGAL-REVIEW",
        "CZ-AT-INT-LEGAL-REVIEW",
        "CZ-AT-ROY-LEGAL-REVIEW",
        "CZ-CH-DIV-LEGAL-REVIEW",
        "CZ-CH-INT-LEGAL-REVIEW",
        "CZ-CH-ROY-LEGAL-REVIEW",
        "CZ-GR-DIV-LEGAL-REVIEW",
    }

    assert all(
        rows[packet_id][
            "exception_resolution_applied"
        ]
        is True
        for packet_id in expected
    )


def test_no_source_exception_codes_remain():
    payload = load(
        "global_primary_review_candidates_resolved.json"
    )

    removed_codes = {
        "missing_base_treaty",
        "missing_instrument_chain_or_priority_review_row",
        "missing_rate_candidate",
    }

    for row in payload["scopes"]:
        assert not (
            set(row.get("hard_unresolved_codes", []))
            & removed_codes
        )


def test_resolved_dataset_covers_all_scopes():
    payload = load(
        "global_primary_review_candidates_resolved.json"
    )

    assert len(payload["scopes"]) == 294
    assert len({
        row["packet_id"]
        for row in payload["scopes"]
    }) == 294


def test_outputs_remain_fail_closed():
    payload = load(
        "global_primary_review_candidates_resolved.json"
    )

    assert payload["fail_closed"] is True
    assert (
        payload["promotable_to_active_rules"]
        is False
    )
