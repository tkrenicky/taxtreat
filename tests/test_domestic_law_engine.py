import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taxtreat.engine.domestic_law_engine import DomesticLawEngine
from taxtreat.engine.models import ConditionType, Rule, WHTCondition, WHTRate


def build_domestic_rule() -> Rule:
    return Rule(
        article=1,
        transaction_type="dividend",
        rate=15.0,
        rates=[
            WHTRate(
                rate=15.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="==",
                        value="true",
                        description="beneficial owner required",
                    )
                ],
                legal_basis="Domestic law",
                priority=0,
            )
        ],
        conditions=[
            WHTCondition(
                condition_type=ConditionType.beneficial_owner,
                operator="==",
                value="true",
                description="beneficial owner required",
            )
        ],
        legal_basis="Domestic law",
    )


def test_domestic_engine_evaluates_rate_and_exemption():
    engine = DomesticLawEngine()
    rule = build_domestic_rule()

    result = engine.evaluate(
        rule,
        {
            "beneficial_owner": True,
            "entity_type": "company",
            "documentation_complete": True,
        },
        effective_date=date(2024, 1, 1),
    )

    assert result.rate == 15.0
    assert result.eligible is True
    assert result.requires_review is False
    assert result.exemption_applied is False


def test_domestic_engine_supports_exemptions():
    engine = DomesticLawEngine()
    rule = build_domestic_rule()

    result = engine.evaluate(
        rule,
        {
            "beneficial_owner": True,
            "entity_type": "company",
            "documentation_complete": True,
            "exempt": True,
        },
        effective_date=date(2024, 1, 1),
    )

    assert result.rate == 0.0
    assert result.exemption_applied is True
    assert result.eligible is True


def test_domestic_engine_uses_shared_numeric_condition_parsing():
    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        transaction_type="dividend",
        rates=[
            WHTRate(
                rate=10.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10%",
                        unit="%",
                    )
                ],
                legal_basis="Domestic law",
            )
        ],
        legal_basis="Domestic law",
    )

    result = engine.evaluate(rule, {"ownership": 12}, effective_date=date(2024, 1, 1))

    assert result.eligible is True
    assert result.rate == 10.0
    assert result.requires_review is False


def test_domestic_engine_requires_review_for_missing_facts():
    engine = DomesticLawEngine()
    rule = build_domestic_rule()

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.requires_review is True
    assert result.eligible is False
    assert "beneficial_owner" in result.missing_facts


def test_domestic_engine_respects_effective_date():
    engine = DomesticLawEngine()
    rule = build_domestic_rule()
    rule.effective_date = date(2030, 1, 1)

    result = engine.evaluate(rule, {"beneficial_owner": True}, effective_date=date(2024, 1, 1))

    assert result.requires_review is True
    assert result.eligible is False
