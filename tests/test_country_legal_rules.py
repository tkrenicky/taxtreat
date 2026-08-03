from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import CanonicalAnalysisRequest, analyze_transaction

def decide(country: str, facts: dict, determinations: dict | None = None):
    recipient = {"rakousko": "AT", "svycarsko": "CH"}[country]
    return analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="CZ",
            recipient_country=recipient,
            income_type=facts["income_type"],
            transaction_date=date(2026, 8, 3),
            facts=facts,
            determinations=determinations or {},
        )
    )


def test_austria_interest_candidate_is_not_final_before_approval():
    result = decide(
        "rakousko",
        {
            "income_type": "interest",
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
        },
        {"treaty_ppt_passed": True},
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None
    assert result.candidate_rate == 0.0


def test_austria_royalty_candidates_are_not_final_before_approval():
    common = {
        "income_type": "royalty",
        "recipient_is_treaty_resident": True,
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
        "arm_length_amount": True,
        "recipient_is_qualifying_company": False,
    }

    industrial = decide(
        "rakousko",
        {**common, "royalty_category": "industrial"},
        {"treaty_ppt_passed": True},
    )
    copyright_result = decide(
        "rakousko",
        {**common, "royalty_category": "copyright"},
        {"treaty_ppt_passed": True},
    )

    assert industrial.status == DecisionStatus.REVIEW_REQUIRED
    assert industrial.rate is None
    assert industrial.candidate_rate == 5.0
    assert copyright_result.status == DecisionStatus.REVIEW_REQUIRED
    assert copyright_result.rate is None
    assert copyright_result.candidate_rate == 0.0


def test_switzerland_interest_candidate_is_not_final_before_approval():
    result = decide(
        "svycarsko",
        {
            "income_type": "interest",
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
        },
        {"treaty_ppt_passed": True},
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None
    assert result.candidate_rate == 0.0


def test_switzerland_legal_fact_cannot_be_supplied_as_transaction_fact():
    result = decide(
        "svycarsko",
        {
            "income_type": "royalty",
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
        {"treaty_ppt_passed": True},
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
    assert result.candidate_rate == 5.0


def test_switzerland_royalty_missing_protocol_fact_requires_review():
    result = decide(
        "svycarsko",
        {
            "income_type": "royalty",
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
        },
        {"treaty_ppt_passed": True},
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
    assert result.candidate_rate == 5.0
