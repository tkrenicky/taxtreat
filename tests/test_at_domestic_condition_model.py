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

    assert data["schema_version"] == 2
    assert data["source_country"] == "AT"
    assert data["status"] == "candidate_model_not_released"
    assert "AT" not in supported_source_countries()
    assert data["legal_ordering"][:2] == ["domestic_scope", "domestic_non_rate_relief"]
    assert "withholding_due_at_payment" in data["decision_dimensions"]
    assert "refund_eligibility" in data["decision_dimensions"]


def test_at_dividend_eu_parent_relief_keeps_substantive_and_collection_states_separate():
    data = _model()
    relief = data["income_types"]["dividend"]["eu_parent_relief"]

    assert relief["legal_basis"] == "§ 94 Z 2 EStG 1988"
    assert relief["candidate_treatment"] == "domestic_exemption"
    assert relief["minimum_participation_percent"] == 10
    assert relief["minimum_holding_period_months"] == 12
    assert relief["holding_period_must_be_uninterrupted"] is True
    assert relief["source_relief_requires_holding_period_already_completed"] is True
    assert relief["incomplete_holding_period_collection_mechanism"] == "provisional_withholding_then_refund_candidate"
    assert relief["treaty_may_still_reduce_provisional_withholding"] is True


def test_at_dividend_portfolio_refund_never_becomes_source_exemption():
    relief = _model()["income_types"]["dividend"]["portfolio_refund_relief"]

    assert relief["legal_basis"] == "§ 21 Abs. 1 Z 1a KStG 1988"
    assert relief["candidate_treatment"] == "post_withholding_refund_only"
    assert relief["third_country_candidate_requires_participation_below_percent"] == 10
    assert relief["refund_limited_to_wht_not_creditable_in_residence_state"] is True
    assert relief["must_never_be_represented_as_relief_at_source"] is True


def test_at_current_corporate_interest_model_uses_section_98_exclusion_not_legacy_declaration_gate():
    base = _model()["income_types"]["interest"]["base_domestic_layer"]

    assert base["legal_basis"] == ["§ 98 Abs. 1 Z 5 EStG 1988"]
    assert base["corporate_recipient_current_treatment_candidate"] == "outside_limited_tax_liability"
    assert base["corporate_recipient_candidate_rate_percent"] == 0
    assert base["legacy_written_declaration_conditions_not_used_as_current_corporate_eligibility_gate"] is True
    assert base["special_section_99_interest_categories_require_separate_classification"] is True


def test_at_section_99a_relief_models_current_source_and_refund_requirements():
    data = _model()

    for income_type in ("interest", "royalty"):
        relief = data["income_types"][income_type]["eu_interest_royalty_relief"]
        assert relief["legal_basis"] == "§ 99a EStG 1988"
        assert relief["candidate_treatment"] == "domestic_exemption"
        assert relief["beneficial_owner_required"] is True
        assert relief["minimum_direct_participation_percent"] == 25
        assert relief["reverse_direct_participation_alternative_percent"] == 25
        assert relief["common_parent_direct_participation_alternative_percent"] == 25
        assert relief["minimum_holding_period_months"] == 12
        assert relief["confirmations_must_be_available_at_payment_for_source_relief"] is True
        assert relief["refund_route_if_holding_period_or_confirmation_missing_at_payment"] is True
        assert relief["profit_participating_claim_excluded"] is True
        assert relief["anti_avoidance_or_abuse_excluded"] is True
        assert relief["excess_over_arm_length_not_exempt"] is True


def test_at_royalty_twenty_percent_is_candidate_only_for_statutory_route_and_consulting_is_separate():
    data = _model()
    base = data["income_types"]["royalty"]["base_domestic_layer"]

    assert base["candidate_rate_percent"] == 20
    assert base["candidate_treatment"] == "taxable_at_rate"
    assert base["status"] == "category_mapping_required_before_release"
    assert base["technical_or_commercial_consulting_must_not_be_classified_as_royalty"] is True
    assert base["fail_closed"] is True
    constraints = "\n".join(data["semantic_constraints"])
    assert "not a generic Austrian royalty rate" in constraints


def test_at_treaty_relief_at_source_is_procedural_not_substantive_treaty_logic():
    data = _model()
    layer = data["procedural_relief_layer"]

    assert layer["framework"].startswith("DBA-Entlastungsverordnung")
    assert layer["substantive_treaty_entitlement_is_separate"] is True
    assert layer["relief_at_source_requires_documentation"] is True
    assert layer["relief_at_source_is_optional_for_payer"] is True
    assert layer["refund_route_available_if_source_relief_not_used_or_not_permitted"] is True
    assert layer["treaty_rate_must_not_be_equated_with_amount_withheld_at_payment"] is True


def test_at_faster_is_future_only_and_cannot_change_2026_result():
    faster = _model()["future_law"]["faster_directive"]
    assert faster["status"] == "future_only_not_current_decision_logic"
    assert faster["application_from"] == "2030-01-01"
    assert faster["must_not_change_2026_result"] is True
