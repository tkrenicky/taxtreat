from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import evaluate_legal_rules
from taxtreat.engine.legal_rule_loader import load_legal_rules


RULE_DIR = Path("data/legal_rules")


def decide(country: str, facts: dict):
    rules = load_legal_rules(RULE_DIR / f"{country}.json")
    return evaluate_legal_rules(rules, facts, as_of=date(2026, 8, 3))


def test_austria_interest_is_exempt_when_conditions_are_met():
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

    assert result.eligible is True
    assert result.rate == 0.0
    assert result.selected_rule_id == "CZ-AT-INT-BASE"


def test_austria_royalty_categories_produce_different_rates():
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

    assert industrial.rate == 5.0
    assert industrial.selected_rule_id == "CZ-AT-ROY-INDUSTRIAL"
    assert copyright_result.rate == 0.0
    assert copyright_result.selected_rule_id == "CZ-AT-ROY-COPYRIGHT"


def test_switzerland_interest_is_exempt_when_conditions_are_met():
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

    assert result.eligible is True
    assert result.rate == 0.0
    assert result.selected_rule_id == "CZ-CH-INT-BASE"


def test_switzerland_royalty_protocol_overrides_ten_percent_base_rate():
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

    assert result.eligible is True
    assert result.rate == 5.0
    assert result.selected_rule_id == "CZ-CH-ROY-PROTOCOL"
    assert result.overridden_rule_id == "CZ-CH-ROY-BASE"


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
        "recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
