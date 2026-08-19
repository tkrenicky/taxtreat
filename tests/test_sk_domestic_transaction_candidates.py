from __future__ import annotations

from taxtreat.tools.evaluate_sk_domestic_transaction_candidates import (
    evaluate_eu_relief_candidate,
    evaluate_registered_pe_exclusion,
)


def _eu_facts(**overrides):
    facts = {
        "recipient_is_legal_person_or_qualifying_pe_of_eu_legal_person": True,
        "recipient_is_eu_taxpayer_or_qualifying_pe": True,
        "recipient_is_beneficial_owner": True,
        "payer_directly_owns_recipient": False,
        "recipient_directly_owns_payer": True,
        "third_eu_legal_person_directly_owns_both": False,
        "direct_capital_percent": 25,
        "holding_period_months": 24,
        "holding_period_will_reach_24_months": False,
    }
    facts.update(overrides)
    return facts


def test_interest_eu_relief_current_exemption_candidate():
    result = evaluate_eu_relief_candidate("interest", _eu_facts())
    assert result["candidate_treatment"] == "current_exemption_candidate"
    assert result["rate_candidate_percent"] == 0
    assert result["refund_route_candidate"] is False


def test_royalty_eu_relief_uses_same_25_percent_24_month_structure():
    result = evaluate_eu_relief_candidate(
        "royalty",
        _eu_facts(
            payer_directly_owns_recipient=True,
            recipient_directly_owns_payer=False,
        ),
    )
    assert result["candidate_treatment"] == "current_exemption_candidate"
    assert result["rate_candidate_percent"] == 0


def test_future_24_month_completion_is_refund_candidate_not_current_zero_rate():
    result = evaluate_eu_relief_candidate(
        "interest",
        _eu_facts(
            holding_period_months=15,
            holding_period_will_reach_24_months=True,
        ),
    )
    assert result["candidate_treatment"] == "future_holding_period_refund_candidate"
    assert result["rate_candidate_percent"] is None
    assert result["refund_route_candidate"] is True
    assert result["refund_locator"] == "§ 43 ods. 21"


def test_under_25_percent_does_not_get_exemption_candidate():
    result = evaluate_eu_relief_candidate(
        "royalty",
        _eu_facts(direct_capital_percent=24.99),
    )
    assert result["candidate_treatment"] == "exemption_conditions_not_met"
    assert result["rate_candidate_percent"] is None


def test_beneficial_owner_is_required():
    result = evaluate_eu_relief_candidate(
        "interest",
        _eu_facts(recipient_is_beneficial_owner=False),
    )
    assert result["candidate_treatment"] == "exemption_conditions_not_met"


def test_missing_eu_relief_fact_is_fail_closed():
    facts = _eu_facts()
    facts.pop("recipient_is_beneficial_owner")
    result = evaluate_eu_relief_candidate("interest", facts)
    assert result["status"] == "blocked_missing_transaction_facts"
    assert "recipient_is_beneficial_owner" in result["missing_facts"]


def test_registered_sk_pe_exclusion_requires_pe_registration_and_attribution():
    result = evaluate_registered_pe_exclusion({
        "recipient_has_sk_permanent_establishment": True,
        "recipient_sk_pe_registered_under_income_tax_act": True,
        "income_attributable_to_registered_sk_pe": True,
    })
    assert result["applies"] is True

    not_attributable = evaluate_registered_pe_exclusion({
        "recipient_has_sk_permanent_establishment": True,
        "recipient_sk_pe_registered_under_income_tax_act": True,
        "income_attributable_to_registered_sk_pe": False,
    })
    assert not_attributable["applies"] is False


def test_registered_pe_exclusion_missing_facts_is_fail_closed():
    result = evaluate_registered_pe_exclusion({
        "recipient_has_sk_permanent_establishment": True,
    })
    assert result["status"] == "blocked_missing_transaction_facts"
    assert result["applies"] is None
