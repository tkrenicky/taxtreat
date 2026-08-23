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

    assert payload["policy"]["mli_is_not_ppt_only"] is True
    assert (
        payload["policy"]["mli_pair_specific_substantive_matching_required"]
        is True
    )

    assert summary["machine_prepared_scopes"] == 225
    assert summary["review_ready_scopes"] == 0
    assert summary["human_reviewed_scopes"] == 0
    assert summary["production_released_scopes"] == 0

    assert summary["mli_relationship_count"] == 46
    assert summary["mli_scope_count"] == 138
    assert summary["mli_substantive_matching_pending_relationship_count"] == 46
    assert summary["mli_substantive_matching_pending_scope_count"] == 138

    assert summary["provisional_instrument_risk_country_counts"] == {
        "ELEVATED": 8,
        "STANDARD": 67,
    }
    assert summary["provisional_instrument_risk_scope_counts"] == {
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


def test_mli_relationships_are_not_treated_as_ppt_only():
    payload = build_machine_preparation()
    by_packet = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    austria_dividend = by_packet["SK-AT-dividend"]
    austria_interest = by_packet["SK-AT-interest"]

    assert austria_dividend["has_mli_effect"] is True
    assert (
        austria_dividend["mli_review"]["match_status"]
        == "pending_pair_specific_notice_review"
    )
    assert austria_dividend["mli_review"]["ppt_only_assumption_allowed"] is False
    assert set(
        austria_dividend["mli_review"]["candidate_result_changing_articles"]
    ) == {"3", "4", "7", "8", "10", "12", "13", "14", "15"}

    assert set(
        austria_interest["mli_review"]["candidate_result_changing_articles"]
    ) == {"3", "4", "7", "10", "12", "13", "14", "15"}

    assert (
        "mli_pair_specific_substantive_review"
        in austria_dividend["review_workstreams"]
    )
    assert (
        "pair_specific_mli_substantive_article_matching_pending"
        in austria_dividend["release_blockers"]
    )
    assert (
        austria_dividend["risk_tier_status"]
        == "provisional_instrument_complexity_only_mli_matching_pending"
    )


def test_non_mli_relationship_does_not_get_mli_matching_blocker():
    payload = build_machine_preparation()
    by_packet = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    united_states = by_packet["SK-US-dividend"]

    assert united_states["has_mli_effect"] is False
    assert (
        united_states["mli_review"]["match_status"]
        == "not_mli_listed_modified"
    )
    assert (
        "pair_specific_mli_substantive_article_matching_pending"
        not in united_states["release_blockers"]
    )


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


def test_first_human_review_sample_is_deterministic_and_fail_closed():
    payload = build_machine_preparation()
    sample = build_first_human_review_sample(payload)

    rows = sample["sample"]

    assert tuple(row["packet_id"] for row in rows) == SAMPLE_PACKET_IDS
    assert sum(row["risk_tier"] == "STANDARD" for row in rows) == 4
    assert sum(row["risk_tier"] == "ELEVATED" for row in rows) == 2
    assert sample["review_ready"] is False
    assert "Primary treaty text" in sample["review_blocker"]
    assert "substantive MLI matching" in sample["review_blocker"]
    assert sample["sample_policy"]["final_risk_requires_mli_pair_matching"] is True


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


def test_sk_mli_wht_relevance_profile_preserves_result_changing_articles():
    path = (
        ROOT
        / "data"
        / "legal_reviews"
        / "sk_outbound"
        / "mli_wht_relevance_profile.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source_country"] == "SK"
    assert payload["policy"]["pair_specific_matching_required"] is True
    assert payload["policy"]["substantive_wht_effect_can_change_result"] is True

    result_changing = {
        article
        for article, detail in payload["articles"].items()
        if detail["can_change_result"] is True
    }
    assert {"3", "4", "7", "8", "10", "12", "13", "14", "15"}.issubset(
        result_changing
    )

    assert payload["articles"]["8"]["income_types"] == ["dividend"]
    assert set(payload["articles"]["10"]["income_types"]) == {
        "dividend", "interest", "royalty"
    }
