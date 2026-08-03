from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus, evaluate_legal_rules
from taxtreat.engine.legal_rule_loader import load_legal_rules


RULE_DIR = Path("data/legal_rules")


def decide(country: str, facts: dict):
    rules = load_legal_rules(RULE_DIR / f"{country}.json")
    return evaluate_legal_rules(rules, facts, as_of=date(2026, 8, 3))


def test_austria_interest_candidate_is_not_final_before_approval():
    result = decide(
        "rakousko",
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "AT",
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
        },
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None


def test_austria_royalty_candidates_are_not_final_before_approval():
    common = {
        "income_type": "royalty",
        "source_country": "CZ",
        "recipient_country": "AT",
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
    }

    industrial = decide(
        "rakousko",
        {**common, "royalty_category": "industrial"},
    )
    copyright_result = decide(
        "rakousko",
        {**common, "royalty_category": "copyright"},
    )

    assert industrial.status == DecisionStatus.REVIEW_REQUIRED
    assert industrial.rate is None
    assert copyright_result.status == DecisionStatus.REVIEW_REQUIRED
    assert copyright_result.rate is None


def test_switzerland_interest_candidate_is_not_final_before_approval():
    result = decide(
        "svycarsko",
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
        },
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None


def test_switzerland_legal_fact_cannot_be_supplied_as_transaction_fact():
    result = decide(
        "svycarsko",
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.eligible is False
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]


def test_switzerland_royalty_missing_protocol_fact_requires_review():
    result = decide(
        "svycarsko",
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
        },
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
