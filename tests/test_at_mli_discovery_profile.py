from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "legal_reviews" / "at_outbound" / "mli_discovery_profile_2026.json"


def _profile() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def test_at_mli_profile_is_discovery_only_and_requires_bilateral_adjudication():
    data = _profile()

    assert data["schema_version"] == 2
    assert data["source_country"] == "AT"
    assert data["status"] == "discovery_only_bilateral_adjudication_required"
    method = data["bilateral_adjudication_method"]
    assert any("partner jurisdiction" in step for step in method)
    assert any("Article 35" in step for step in method)
    assert any("Article 7" in step for step in method)


def test_at_mli_profile_preserves_both_austrian_notification_layers():
    data = _profile()
    layers = data["austrian_notification_layers"]

    assert [row["deposit_or_notification_date"] for row in layers] == [
        "2017-09-22",
        "2023-08-28",
    ]
    assert layers[1]["publication"] == "BGBl. III Nr. 145/2023"
    assert layers[1]["effective_under_depositary_notification"] == "2023-08-30"


def test_at_wht_mli_scope_is_ppt_only_and_article_8_is_reserved():
    scope = _profile()["wht_engine_scope"]

    assert scope["article_7_ppt"] == {
        "austria_position": "accepted",
        "engine_effect": "general_treaty_benefit_abuse_overlay",
        "bilateral_match_required": True,
        "withholding_tax_effective_date_required": True,
    }
    assert scope["article_8_dividend_transfer_transactions"] == {
        "austria_position": "reserved_in_full",
        "engine_effect": "none",
        "bilateral_match_required": False,
        "withholding_tax_effective_date_required": False,
    }
    assert scope["other_mli_articles"]["engine_effect"] == "no_separate_dividend_interest_royalty_rate_branch"


def test_at_mli_release_constraints_fail_closed_on_pair_and_wht_effective_date():
    data = _profile()
    constraints = "\n".join(data["release_constraints"])

    assert "not sufficient evidence of bilateral MLI effect" in constraints
    assert "bilateral matching" in constraints
    assert "Article 35 effective-date analysis" in constraints
    assert "reserved MLI Article 8 in full" in constraints


def test_ppt_overlay_does_not_create_rate_or_holding_period_branch():
    data = _profile()
    assert data["wht_engine_scope"]["article_7_ppt"]["engine_effect"] == "general_treaty_benefit_abuse_overlay"
    assert data["wht_engine_scope"]["article_8_dividend_transfer_transactions"]["engine_effect"] == "none"
