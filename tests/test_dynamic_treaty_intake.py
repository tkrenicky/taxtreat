from __future__ import annotations

from taxtreat.engine.legal_rule_engine import (
    LegalCondition,
    _evaluate_condition,
)
from taxtreat.services.intake import build_intake_plan


def plan(
    country: str,
    income_type: str,
    *missing: str,
):
    return build_intake_plan(
        {
            "source_country": "CZ",
            "recipient_country": country,
            "income_type": income_type,
        },
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": list(missing),
        },
    )


def first_question(result):
    assert result["questions"]
    return result["questions"][0]


def test_al_interest_article_11_3_requires_professional_review():
    question = first_question(
        plan(
            "AL",
            "interest",
            "article_11_3_exemption",
        )
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"
    assert question["input_path"] is None
    assert question["advisor_topic"] == "interest_treaty_special_condition"


def test_br_interest_minimum_term_is_numeric():
    question = first_question(
        plan(
            "BR",
            "interest",
            "minimum_term_years",
        )
    )

    assert question["client_answerable"] is True
    assert question["response_type"] == "number"

    assert (
        question["input_path"]
        == "facts.minimum_term_years"
    )


def test_au_royalty_immediate_entitlement_is_boolean():
    question = first_question(
        plan(
            "AU",
            "royalty",
            "recipient_has_immediate_entitlement",
        )
    )

    assert question["client_answerable"] is True
    assert question["response_type"] == "boolean"

    assert (
        question["input_path"]
        == "facts.recipient_has_immediate_entitlement"
    )


def test_bd_holding_period_uses_acquisition_date():
    question = first_question(
        plan(
            "BD",
            "dividend",
            "continuous_holding_period_days",
        )
    )

    assert question["response_type"] == "date"

    assert (
        question["input_path"]
        == "derived.acquisition_date"
    )


def test_duplicate_acquisition_date_question_is_collapsed():
    result = plan(
        "BD",
        "dividend",
        "holding_period_months",
        "continuous_holding_period_days",
    )

    questions = [
        question
        for question in result["questions"]
        if question.get("client_answerable")
        and question.get("input_path")
        == "derived.acquisition_date"
    ]

    assert len(questions) == 1


def test_ch_royalty_foreign_wht_condition_is_professional():
    question = first_question(
        plan(
            "CH",
            "royalty",
            "recipient_country_imposes_royalty_wht_on_nonresidents",
        )
    )

    assert question["client_answerable"] is False

    assert (
        question["response_type"]
        == "professional_review"
    )

    assert (
        question["advisor_topic"]
        == "royalty_treaty_legal_condition"
    )


def test_es_royalty_residence_tax_condition_is_professional():
    question = first_question(
        plan(
            "ES",
            "royalty",
            "recipient_taxed_on_royalty_in_residence_state",
        )
    )

    assert question["client_answerable"] is False

    assert (
        question["advisor_topic"]
        == "royalty_treaty_legal_condition"
    )


def test_fallback_case_is_internal_rule_control():
    condition = LegalCondition(
        fact="fallback_case",
        operator="==",
        value="all_other_cases",
    )

    satisfied, missing = _evaluate_condition(
        condition,
        {},
        {},
    )

    assert satisfied is True
    assert missing is None


def test_source_state_taxation_is_internal_rule_control():
    condition = LegalCondition(
        fact="source_state_taxation",
        operator="==",
        value="prohibited_under_article_11",
    )

    satisfied, missing = _evaluate_condition(
        condition,
        {},
        {},
    )

    assert satisfied is True
    assert missing is None


def test_general_article_11_rate_is_internal_rule_control():
    condition = LegalCondition(
        fact="general_article_11_2_rate",
        operator="==",
        value="true",
    )

    satisfied, missing = _evaluate_condition(
        condition,
        {},
        {},
    )

    assert satisfied is True
    assert missing is None


def test_pe_inverse_claim_fact_is_explicitly_derived():
    from taxtreat.services.intake import (
        DERIVED_TRANSACTION_FACTS,
    )

    assert (
        DERIVED_TRANSACTION_FACTS[
            "claim_not_effectively_connected_to_czech_pe"
        ]
        == "permanent_establishment_connection"
    )


def test_pe_inverse_royalty_fact_is_explicitly_derived():
    from taxtreat.services.intake import (
        DERIVED_TRANSACTION_FACTS,
    )

    assert (
        DERIVED_TRANSACTION_FACTS[
            "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base"
        ]
        == "permanent_establishment_connection"
    )
