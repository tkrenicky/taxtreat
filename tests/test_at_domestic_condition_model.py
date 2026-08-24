from __future__ import annotations

import json
from pathlib import Path

from taxtreat.countries.registry import supported_source_countries


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data" / "legal_reviews" / "at_outbound" / "domestic_condition_model_2026.json"


def _model() -> dict:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def test_at_domestic_model_is_candidate_only_and_not_runtime_registered():
    data = _model()

    assert data["source_country"] == "AT"
    assert data["status"] == "candidate_model_not_released"
    assert "AT" not in supported_source_countries()
    assert data["legal_ordering"][:2] == ["domestic_scope", "domestic_non_rate_relief"]


def test_at_dividend_eu_parent_relief_is_domestic_exemption_before_treaty():
    data = _model()
    relief = data["income_types"]["dividend"]["eu_parent_relief"]

    assert relief["legal_basis"] == "§ 94 EStG 1988"
    assert relief["candidate_treatment"] == "domestic_exemption"
    assert relief["minimum_participation_percent"] == 10
    assert relief["minimum_holding_period_months"] == 12
    assert relief["holding_period_must_be_uninterrupted"] is True
    assert relief["anti_abuse_review_required"] is True


def test_at_interest_remains_fail_closed_until_source_nexus_is_classified():
    data = _model()
    base = data["income_types"]["interest"]["base_domestic_layer"]

    assert base["candidate_treatment"] is None
    assert base["candidate_rate_percent"] is None
    assert base["status"] == "source_nexus_mapping_required"
    assert base["fail_closed"] is True
    assert any("§ 98" in item for item in base["required_classification"])


def test_at_section_99a_relief_keeps_substantive_source_and_refund_states_separate():
    data = _model()

    for income_type in ("interest", "royalty"):
        relief = data["income_types"][income_type]["eu_interest_royalty_relief"]
        assert relief["legal_basis"] == "§ 99a EStG 1988"
        assert relief["candidate_treatment"] == "domestic_exemption"
        assert relief["beneficial_owner_required"] is True
        assert relief["minimum_direct_participation_percent"] == 25
        assert relief["minimum_holding_period_months"] == 12
        assert relief["documentary_confirmation_required_for_relief_at_source"] is True
        assert relief["refund_route_possible_if_holding_period_or_confirmation_not_yet_available"] is True


def test_at_royalty_twenty_percent_is_candidate_only_for_statutory_route():
    data = _model()
    base = data["income_types"]["royalty"]["base_domestic_layer"]

    assert base["candidate_rate_percent"] == 20
    assert base["candidate_treatment"] == "taxable_at_rate"
    assert base["status"] == "category_mapping_required_before_release"
    assert base["fail_closed"] is True
    constraints = "\n".join(data["semantic_constraints"])
    assert "not a generic Austrian royalty rate" in constraints


def test_at_treaty_relief_at_source_is_procedural_not_substantive_treaty_logic():
    data = _model()
    layer = data["procedural_relief_layer"]

    assert layer["framework"] == "DBA-Entlastungsverordnung"
    assert layer["substantive_treaty_entitlement_is_separate"] is True
    assert layer["relief_at_source_requires_documentation"] is True
    assert layer["refund_route_required_where_source_relief_is_not_permitted"] is True
