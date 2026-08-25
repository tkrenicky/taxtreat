from taxtreat.countries.at_decision_candidate import (
    evaluate_at_wht_candidate,
    evaluate_eu_swiss_article9_candidate,
    evaluate_royalty_collection_basis_candidate,
)


def _net_route(**updates):
    facts = {
        "recipient_is_corporation": True,
        "expense_deduction_option_elected": True,
        "recipient_is_eu_or_eea_resident": True,
        "directly_related_expenses_disclosed_in_writing_before_payment": True,
        "deducted_expense_payee_is_limited_taxpayer": False,
        "deducted_expenses_to_limited_taxpayer_eur": 0,
        "domestic_taxation_of_expense_payee_sufficiently_secured": True,
    }
    facts.update(updates)
    return facts


def _royalty(**updates):
    facts = {
        "royalty_within_section_99_1_3": True,
        "payer_and_recipient_section_99a_entity_conditions_satisfied": False,
        "beneficial_owner": True,
        "section_99a_association_test_satisfied": False,
        "holding_period_months_completed": 0,
        "section_99a_confirmations_available_at_payment": False,
        "tax_avoidance_abuse_trigger": False,
        "profit_participating_claim": False,
        "amount_exceeds_arm_length": False,
        **_net_route(),
    }
    facts.update(updates)
    return facts


def _swiss(**updates):
    facts = {
        "eu_swiss_company_residence_pair_satisfied": True,
        "neither_company_third_state_resident_under_dtt": True,
        "companies_subject_to_corporation_tax_without_exemption": True,
        "companies_are_qualifying_limited_company_forms": True,
        "eu_swiss_anti_abuse_clear": True,
        "direct_ownership_percent": 25,
        "eu_swiss_association_25_percent_test_satisfied": True,
        "holding_period_months_completed": 24,
    }
    facts.update(updates)
    return facts


def test_corporate_royalty_net_route_is_23_percent_on_net_base_not_25_percent_on_gross():
    result = evaluate_royalty_collection_basis_candidate(_net_route())
    assert result["selected_route_candidate"] == "section_99_net_expense_basis_corporate"
    net = result["collection_candidates"][1]
    assert net["rate_percent_candidate"] == 23.0
    assert net["withholding_base"] == "net_revenue_after_admissible_direct_expenses"
    assert result["policy"]["gross_and_net_rates_have_different_tax_bases"] is True
    assert result["policy"]["section_99_expense_security_threshold_eur"] == 2463.0


def test_noncorporate_net_route_preserves_current_20k_progressive_schedule():
    result = evaluate_royalty_collection_basis_candidate(
        _net_route(recipient_is_corporation=False)
    )
    schedule = result["collection_candidates"][1]["rate_schedule_candidate"]
    assert schedule == [
        {"up_to_calendar_year_income_eur": 20000.0, "rate_percent": 20.0},
        {"above_calendar_year_income_eur": 20000.0, "rate_percent": 25.0},
    ]


def test_net_expense_route_fails_back_to_gross_if_section_99_expense_payee_security_fails():
    result = evaluate_royalty_collection_basis_candidate(
        _net_route(
            deducted_expense_payee_is_limited_taxpayer=True,
            deducted_expenses_to_limited_taxpayer_eur=3000,
            domestic_taxation_of_expense_payee_sufficiently_secured=False,
        )
    )
    assert result["selected_route_candidate"] == "section_99_gross_basis"
    assert "section_99_2_2_expense_payee_domestic_taxation_not_secured" in result["legal_blockers"]
    assert result["review_required"] is True


def test_gross_royalty_route_remains_20_percent_when_net_option_not_elected():
    result = evaluate_royalty_collection_basis_candidate(
        _net_route(expense_deduction_option_elected=False)
    )
    assert result["selected_route_candidate"] == "section_99_gross_basis"
    assert result["collection_candidates"][0]["rate_percent_candidate"] == 20.0
    assert result["collection_candidates"][0]["withholding_base"] == "gross_revenue"


def test_current_eu_swiss_article9_dividend_candidate_requires_25_percent_for_two_years():
    eligible = evaluate_eu_swiss_article9_candidate(
        recipient_country="CH", income_type="dividend", facts=_swiss()
    )
    assert eligible["eligible_candidate"] is True
    assert eligible["source_tax_rate_percent_candidate"] == 0.0
    assert eligible["existing_more_favourable_dtt_unaffected"] is True

    short = evaluate_eu_swiss_article9_candidate(
        recipient_country="CH",
        income_type="dividend",
        facts=_swiss(holding_period_months_completed=23),
    )
    assert short["eligible_candidate"] is False
    assert "eu_swiss_article9_two_year_holding_not_satisfied" in short["legal_blockers"]


def test_current_eu_swiss_article9_interest_and_royalty_use_association_test():
    for income_type in ("interest", "royalty"):
        result = evaluate_eu_swiss_article9_candidate(
            recipient_country="CH", income_type=income_type, facts=_swiss()
        )
        assert result["eligible_candidate"] is True
        assert result["must_be_compared_with_dtt"] is True


def test_non_swiss_recipient_never_gets_swiss_special_relief_candidate():
    assert evaluate_eu_swiss_article9_candidate(
        recipient_country="DE", income_type="royalty", facts=_swiss()
    ) is None


def test_complete_at_orchestrator_keeps_royalty_domestic_basis_visible_when_section_99a_fails():
    result = evaluate_at_wht_candidate(
        recipient_country="US",
        income_type="royalty",
        facts=_royalty(),
    )
    assert result["domestic_precedence"]["continue_to_treaty_for_current_withholding"] is True
    assert result["royalty_domestic_collection_basis"]["selected_route_candidate"] == "section_99_net_expense_basis_corporate"
    assert result["final_payment_date_withholding_rate_percent"] is None
    assert result["production_release_allowed"] is False


def test_complete_at_orchestrator_can_record_treaty_source_relief_without_releasing_production():
    result = evaluate_at_wht_candidate(
        recipient_country="US",
        income_type="royalty",
        facts=_royalty(expense_deduction_option_elected=False),
        treaty_rate_percent=5,
        treaty_substantive_entitlement_confirmed=True,
        treaty_relief_at_source_documentation_ready=True,
        treaty_relief_at_source_restricted_for_case=False,
    )
    assert result["treaty_collection"]["withholding_rate_now_candidate"] == 5.0
    assert result["final_payment_date_withholding_rate_percent"] == 5.0
    assert result["selected_legal_route"] == "treaty_relief_at_source_candidate"
    assert result["production_release_allowed"] is False


def test_swiss_article9_zero_is_kept_parallel_to_dtt_and_still_requires_review():
    facts = _royalty(**_swiss())
    result = evaluate_at_wht_candidate(
        recipient_country="CH",
        income_type="royalty",
        facts=facts,
        treaty_rate_percent=0,
        treaty_substantive_entitlement_confirmed=True,
        treaty_relief_at_source_documentation_ready=True,
        treaty_relief_at_source_restricted_for_case=False,
    )
    assert result["eu_swiss_article9_candidate"]["eligible_candidate"] is True
    assert result["treaty_collection"]["withholding_rate_now_candidate"] == 0.0
    assert result["final_payment_date_withholding_rate_percent"] == 0.0
    assert result["review_required"] is True
