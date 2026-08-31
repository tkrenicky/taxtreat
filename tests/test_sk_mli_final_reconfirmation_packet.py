from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "data" / "legal_reviews" / "sk_outbound"

PACKET = SK / "mli_final_reconfirmation_packet_2026.json"
MANIFEST = SK / "source_country_release_manifest.json"

POSITIVE = {
    "BE", "CA", "DE", "ES", "IE", "IL", "IN",
    "KZ", "NL", "RS", "SI", "TN", "ZA",
}
NEGATIVE = {"GB", "KR", "LU", "VN"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_packet_locks_corrected_article_8_population():
    packet = load(PACKET)

    assert set(
        packet["locked_article_8_population"]["positive"]
    ) == POSITIVE

    assert set(
        packet["locked_article_8_population"]
        ["negative_regressions"]
    ) == NEGATIVE


def test_packet_contains_exact_four_review_corrections():
    packet = load(PACKET)

    corrections = packet[
        "corrections_requiring_reconfirmation"
    ]

    assert {
        row["recipient_country"]
        for row in corrections
    } == NEGATIVE

    assert all(
        row["article_8_365_day_test_applies"] is False
        for row in corrections
    )

    assert all(
        row["machine_extraction_was_correct"] is True
        for row in corrections
    )


def test_packet_records_explicit_reviewer_reconfirmation():
    packet = load(PACKET)
    confirmation = packet["reviewer_confirmation"]

    assert packet["status"] == "RECONFIRMED"
    assert confirmation["confirmed"] is True
    assert (
        confirmation["confirmed_by"]
        == "explicit_user_reviewer_confirmation"
    )
    assert confirmation["confirmed_at"] == "2026-08-21T08:44:27Z"
    assert (
        confirmation["confirmation_statement"]
        == packet["required_confirmation_statement"]
    )


def test_reconfirmation_is_complete_but_release_waits_for_rule_materialization():
    packet = load(PACKET)
    manifest = load(MANIFEST)

    assert packet["reviewer_confirmation"]["confirmed"] is True

    assert manifest["release_eligible"] is False
    assert manifest["release_status"] == "pre_release"
    assert manifest["blockers"] == ["structured_sk_treaty_rules_not_materialized"]

    assert (
        manifest["mli_final_reviewer_reconfirmation_required"]
        is False
    )
    assert (
        manifest["mli_final_reviewer_reconfirmation_completed"]
        is True
    )
    assert (
        manifest["mli_final_reviewer_reconfirmation_evidence"]
        == "mli_final_reconfirmation_packet_2026.json"
    )
