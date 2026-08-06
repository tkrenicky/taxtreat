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


def test_language_policy_is_fail_closed():
    policy = load("source_language_policy.json")

    assert policy["working_language"] == "en"
    assert policy["fail_closed"] is True
    assert (
        policy["principles"]
        ["damaged_ocr_may_support_active_rule"]
        is False
    )


def test_all_seven_exceptions_have_resolution():
    payload = load(
        "source_exception_resolutions.json"
    )

    rows = payload["resolutions"]

    assert len(rows) == 7
    assert len({
        row["packet_id"]
        for row in rows
    }) == 7


def test_resolution_overlay_is_not_promotable():
    payload = load(
        "source_exception_resolutions.json"
    )

    assert payload["fail_closed"] is True
    assert (
        payload["promotable_to_active_rules"]
        is False
    )


def test_all_resolutions_have_rate_candidates():
    payload = load(
        "source_exception_resolutions.json"
    )

    assert all(
        row["candidate_rates"]
        for row in payload["resolutions"]
    )


def test_damaged_pilot_ocr_requires_replacement():
    payload = load(
        "source_exception_resolutions.json"
    )

    pilot_rows = [
        row
        for row in payload["resolutions"]
        if row["packet_id"].startswith(
            ("CZ-AT-", "CZ-CH-")
        )
    ]

    assert len(pilot_rows) == 6
    assert all(
        row["text_quality_status"]
        == "ocr_rejected"
        for row in pilot_rows
    )
    assert all(
        row["clean_english_source_required"]
        is True
        for row in pilot_rows
    )
