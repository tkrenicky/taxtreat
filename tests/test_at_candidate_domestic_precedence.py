import pytest

from taxtreat.countries.at_candidate import (
    evaluate_candidate_domestic_precedence,
    evaluate_section_99a_candidate,
    evaluate_treaty_collection_mechanism,
)


def _dividend(**updates):
    facts = {
        "recipient_is_corporation": True,
        "recipient_is_qualifying_eu_parent": True,
        "ownership_percent": 10,
        "holding_period_months_completed": 12,
        "anti_abuse_or_hidden_distribution_trigger": False,
        "recipient_is_eu_or_eea_resident": True,
        "recipient_state_has_comprehensive_administrative_assistance": True,
        "wht_creditable_in_residence_state": True,
    }
    facts.update(updates)
    return facts


def _section_99a(**updates):
    facts = {
        "royalty_within_section_99_1_3": True,
        "payer_and_recipient_section_99a_entity_conditions_satisfied": True,
        "beneficial_owner": True,
        "section_99a_association_test_satisfied": True,
        "holding_period_months_completed": 12,
        "section_99a_confirmations_available_at_payment": True,
        "tax_avoidance_abuse_trigger": False,
        "profit_participating_claim": False,
        "amount_exceeds_arm_length": False,
    }
    facts.update(updates)
    return facts


def test_at_eu_parent_dividend_exemption_precedes_treaty():
    result = evaluate_candidate_domestic_precedence(income_type="dividend", facts=_dividend())
    assert result["substantive_treatment_candidate"] == "domestic_exemption"
    assert result["withholding_rate_now_candidate"] == 0.0
    assert result["relief_mechanism_candidate"] == "relief_at_source"
    assert result["continue_to_treaty_for_current_withholding"] is False
    assert result["production_release_allowed"] is False


def test_at_dividend_incomplete_holding_period_withholds_then_refunds_and_still_checks_treaty():
    result = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts=_dividend(holding_period_months_completed=5),
    )
    assert result["substantive_treatment_candidate"] == "directive_relief_candidate_after_holding_period"
    assert result["withholding_rate_now_candidate"] is None
    assert result["relief_mechanism_candidate"] == "provisional_withholding_then_refund"
    assert result["refund_candidate"] is True
    assert result["continue_to_treaty_for_current_withholding"] is True


def test_at_dividend_source_relief_anti_abuse_block_does_not_become_false_zero_rate():
    result = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts=_dividend(anti_abuse_or_hidden_distribution_trigger=True),
    )
    assert result["withholding_rate_now_candidate"] is None
    assert result["relief_mechanism_candidate"] == "withholding_then_refund_review"
    assert "anti_abuse_or_hidden_distribution_source_relief_block" in result["legal_blockers"]
    assert result["review_required"] is True


def test_at_portfolio_dividend_refund_is_post_withholding_remedy_only():
    result = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts=_dividend(
            recipient_is_qualifying_eu_parent=False,
            ownership_percent=5,
            wht_creditable_in_residence_state=False,
        ),
    )
    assert result["substantive_treatment_candidate"] == "taxable_subject_to_treaty"
    assert result["refund_candidate"] is True
    assert result["withholding_rate_now_candidate"] is None
    assert result["continue_to_treaty_for_current_withholding"] is True


def test_at_portfolio_dividend_missing_refund_facts_and_third_country_assistance_paths_are_explicit():
    missing = _dividend(recipient_is_qualifying_eu_parent=False, ownership_percent=5)
    missing.pop("wht_creditable_in_residence_state")
    result = evaluate_candidate_domestic_precedence(income_type="dividend", facts=missing)
    assert "wht_creditable_in_residence_state" in result["missing_facts"]
    assert result["refund_candidate"] is False

    third = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts=_dividend(
            recipient_is_qualifying_eu_parent=False,
            recipient_is_eu_or_eea_resident=False,
            recipient_state_has_comprehensive_administrative_assistance=True,
            ownership_percent=5,
            wht_creditable_in_residence_state=False,
        ),
    )
    assert third["refund_candidate"] is True


def test_at_noncorporate_dividend_does_not_invent_corporate_domestic_rate():
    result = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts=_dividend(
            recipient_is_corporation=False,
            recipient_is_qualifying_eu_parent=False,
        ),
    )
    assert result["domestic_rate_percent_candidate"] is None
    assert result["continue_to_treaty_for_current_withholding"] is True


def test_at_corporate_interest_is_outside_limited_tax_liability_under_current_section_98():
    result = evaluate_candidate_domestic_precedence(
        income_type="interest",
        facts={
            "recipient_is_natural_person": False,
            "interest_is_special_section_99_category": False,
        },
    )
    assert result["substantive_treatment_candidate"] == "outside_limited_tax_liability"
    assert result["withholding_rate_now_candidate"] == 0.0
    assert result["continue_to_treaty_for_current_withholding"] is False


def test_at_interest_missing_classification_facts_fail_closed_and_special_interest_routes_to_99a():
    missing = evaluate_candidate_domestic_precedence(
        income_type="interest", facts={"recipient_is_natural_person": False}
    )
    assert "interest_is_special_section_99_category" in missing["missing_facts"]

    facts = _section_99a()
    facts.update({
        "recipient_is_natural_person": False,
        "interest_is_special_section_99_category": True,
    })
    special = evaluate_candidate_domestic_precedence(income_type="interest", facts=facts)
    assert special["substantive_treatment_candidate"] == "domestic_exemption"


def test_at_royalty_section_99a_relief_at_source_requires_all_current_conditions():
    result = evaluate_candidate_domestic_precedence(income_type="royalty", facts=_section_99a())
    assert result["substantive_treatment_candidate"] == "domestic_exemption"
    assert result["domestic_rate_percent_candidate"] == 0.0
    assert result["withholding_rate_now_candidate"] == 0.0


def test_at_royalty_incomplete_holding_or_missing_confirmation_uses_refund_path_not_zero_now():
    for changes in (
        {"holding_period_months_completed": 9},
        {"section_99a_confirmations_available_at_payment": False},
    ):
        result = evaluate_candidate_domestic_precedence(
            income_type="royalty",
            facts=_section_99a(**changes),
        )
        assert result["substantive_treatment_candidate"] == "section_99a_refund_candidate"
        assert result["withholding_rate_now_candidate"] is None
        assert result["refund_candidate"] is True
        assert result["continue_to_treaty_for_current_withholding"] is True


def test_at_section_99a_exclusions_fail_closed_and_continue_to_treaty():
    cases = (
        ("tax_avoidance_abuse_trigger", True, "section_99a_anti_abuse_exclusion"),
        ("profit_participating_claim", True, "profit_participating_claim_excluded_from_section_99a"),
        ("amount_exceeds_arm_length", True, "section_99a_only_arm_length_amount_can_be_exempt"),
        ("beneficial_owner", False, "beneficial_owner_not_satisfied"),
        ("section_99a_association_test_satisfied", False, "section_99a_association_test_not_satisfied"),
        (
            "payer_and_recipient_section_99a_entity_conditions_satisfied",
            False,
            "section_99a_entity_or_tax_conditions_not_satisfied",
        ),
    )
    for fact, value, blocker in cases:
        result = evaluate_candidate_domestic_precedence(
            income_type="royalty",
            facts=_section_99a(**{fact: value}),
        )
        assert result["substantive_treatment_candidate"] == "taxable_subject_to_treaty"
        assert blocker in result["legal_blockers"]
        assert result["withholding_rate_now_candidate"] is None


def test_at_section_99a_missing_facts_and_invalid_income_type_fail_closed():
    facts = _section_99a()
    facts.pop("beneficial_owner")
    result = evaluate_section_99a_candidate("royalty", facts)
    assert "beneficial_owner" in result["missing_facts"]
    assert result["domestic_rate_percent_candidate"] == 20.0

    with pytest.raises(ValueError, match="only to interest or royalty"):
        evaluate_section_99a_candidate("dividend", _section_99a())


def test_at_royalty_domestic_twenty_percent_is_not_applied_until_section_99_classification():
    result = evaluate_candidate_domestic_precedence(
        income_type="royalty",
        facts={"royalty_within_section_99_1_3": False},
    )
    assert result["domestic_rate_percent_candidate"] is None
    assert result["withholding_rate_now_candidate"] is None
    assert result["review_required"] is True

    missing = evaluate_candidate_domestic_precedence(income_type="royalty", facts={})
    assert "royalty_within_section_99_1_3" in missing["missing_facts"]


def test_at_treaty_rate_and_collection_mechanism_are_separate_states():
    source = evaluate_treaty_collection_mechanism(
        treaty_rate_percent=5,
        treaty_substantive_entitlement_confirmed=True,
        relief_at_source_documentation_ready=True,
        relief_at_source_restricted_for_case=False,
    )
    assert source["withholding_rate_now_candidate"] == 5.0
    assert source["relief_mechanism_candidate"] == "treaty_relief_at_source"

    refund = evaluate_treaty_collection_mechanism(
        treaty_rate_percent=5,
        treaty_substantive_entitlement_confirmed=True,
        relief_at_source_documentation_ready=False,
        relief_at_source_restricted_for_case=False,
    )
    assert refund["withholding_rate_now_candidate"] is None
    assert refund["refund_candidate"] is True
    assert refund["relief_mechanism_candidate"] == "domestic_withholding_then_treaty_refund"

    restricted = evaluate_treaty_collection_mechanism(
        treaty_rate_percent=5,
        treaty_substantive_entitlement_confirmed=True,
        relief_at_source_documentation_ready=True,
        relief_at_source_restricted_for_case=True,
    )
    assert restricted["withholding_rate_now_candidate"] is None
    assert restricted["refund_candidate"] is True

    unresolved = evaluate_treaty_collection_mechanism(
        treaty_rate_percent=None,
        treaty_substantive_entitlement_confirmed=True,
        relief_at_source_documentation_ready=True,
        relief_at_source_restricted_for_case=False,
    )
    assert unresolved["status"] == "unresolved"


def test_at_missing_domestic_precedence_facts_never_silently_fall_through_to_treaty():
    result = evaluate_candidate_domestic_precedence(
        income_type="dividend",
        facts={"recipient_is_corporation": True},
    )
    assert result["review_required"] is True
    assert result["continue_to_treaty_for_current_withholding"] is False
    assert "ownership_percent" in result["missing_facts"]


def test_at_unsupported_income_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported AT income type"):
        evaluate_candidate_domestic_precedence(income_type="capital_gain", facts={})
