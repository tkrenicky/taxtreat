from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "sk_outbound"
    / "pilot_human_review_evidence.json"
)


def _payload():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_pilot_review_pack_is_fail_closed_and_partially_review_ready():
    payload = _payload()

    assert payload["source_country"] == "SK"
    assert payload["policy"]["primary_sources_required"] is True
    assert payload["policy"]["mli_pair_specific_matching_required"] is True
    assert payload["policy"]["review_ready_does_not_mean_approved"] is True
    assert payload["policy"]["runtime_release"] is False

    assert payload["summary"] == {
        "sample_scope_count": 6,
        "review_ready_scopes": 3,
        "blocked_scopes": 3,
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
    }

    scopes = payload["scopes"]
    assert len(scopes) == 6
    assert len({row["packet_id"] for row in scopes}) == 6

    assert sum(
        row["review_status"] == "ready_for_human_review"
        for row in scopes
    ) == 3
    assert sum(
        row["review_status"].startswith("blocked_")
        for row in scopes
    ) == 3


def test_non_mli_pilot_dividend_rules_are_precise():
    by_id = {row["packet_id"]: row for row in _payload()["scopes"]}

    us = by_id["SK-US-dividend"]
    assert us["mli"]["applies"] is False
    assert us["base_treaty"]["operative_article"] == "Article 10"
    assert us["base_treaty"]["source_state_rate_rule"]["qualifying_rate_percent"] == 5
    assert us["base_treaty"]["source_state_rate_rule"]["general_rate_percent"] == 15
    assert "10 percent" in " ".join(
        us["base_treaty"]["source_state_rate_rule"]["qualifying_conditions"]
    )

    nz = by_id["SK-NZ-dividend"]
    assert nz["mli"]["applies"] is False
    assert nz["base_treaty"]["source_state_rate_rule"]["qualifying_rate_percent"] == 5
    assert nz["base_treaty"]["source_state_rate_rule"]["general_rate_percent"] == 15
    conditions = " ".join(
        nz["base_treaty"]["source_state_rate_rule"]["qualifying_conditions"]
    )
    assert "10 percent" in conditions
    assert "365-day" in conditions


def test_austria_interest_preserves_result_changing_mli_guards():
    by_id = {row["packet_id"]: row for row in _payload()["scopes"]}
    at = by_id["SK-AT-interest"]

    assert at["review_status"] == "ready_for_human_review"
    assert at["base_treaty"]["source_state_rate_rule"]["ordinary_treaty_rate_percent"] == 0
    assert at["mli"]["applies"] is True
    assert at["mli"]["wht_effective_from"] == "2019-01-01"

    articles = {
        row["mli_article"]
        for row in at["mli"]["matched_effects_relevant_to_interest"]
    }
    assert {"7", "10", "13", "15"}.issubset(articles)
    assert "19 percent" in at["candidate_conclusion"]["fallback_if_treaty_benefit_denied"]
    assert "35 percent" in at["candidate_conclusion"]["fallback_if_treaty_benefit_denied"]
    assert "EU" in at["candidate_conclusion"]["eu_relief_overlay"]


def test_unfinished_instrument_chains_cannot_be_human_review_ready():
    by_id = {row["packet_id"]: row for row in _payload()["scopes"]}

    for packet_id in (
        "SK-AU-royalty",
        "SK-NL-royalty",
        "SK-GB-interest",
    ):
        row = by_id[packet_id]
        assert row["review_status"].startswith("blocked_")
        assert row["blockers"]
