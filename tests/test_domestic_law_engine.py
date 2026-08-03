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

def test_domestic_engine_no_rates():
    engine = DomesticLawEngine()
    rule = Rule(article=1, transaction_type="dividend")

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.requires_review is True
    assert result.eligible is False


def test_domestic_engine_zero_rate_rule():
    engine = DomesticLawEngine()
    rule = Rule(article=1, transaction_type="dividend", rate=0, rates=[WHTRate(rate=0)])

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.rate == 0.0
    assert result.eligible is True


def test_domestic_engine_invalid_article():
    engine = DomesticLawEngine()
    rule = Rule(article=0, transaction_type="dividend", rates=[WHTRate(rate=15)])

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.requires_review is True


def test_domestic_engine_recipient_type():
    engine = DomesticLawEngine()

    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.recipient_type,
                        value="company",
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {"entity_type": "company"}, effective_date=date(2024, 1, 1))

    assert result.eligible
    assert result.rate == 5


def test_domestic_engine_pe_connection():
    engine = DomesticLawEngine()

    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.permanent_establishment_connection,
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {"permanent_establishment": True}, effective_date=date(2024, 1, 1))

    assert result.eligible
    assert result.rate == 5


def test_domestic_engine_future_rate_not_effective():
    engine = DomesticLawEngine()

    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5,
                effective_date=date(2035, 1, 1),
            )
        ],
    )

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.requires_review is True


def test_domestic_engine_missing_entity_type():
    engine = DomesticLawEngine()

    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.recipient_type,
                        value="company",
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert "entity_type" in result.missing_facts


def test_domestic_engine_missing_pe():
    engine = DomesticLawEngine()

    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.permanent_establishment_connection,
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert "permanent_establishment" in result.missing_facts



def test_domestic_engine_rate_without_conditions_applies():
    engine = DomesticLawEngine()
    rule = Rule(article=1, rates=[WHTRate(rate=15.0)])

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.eligible is True
    assert result.rate == 15.0
    assert result.requires_review is False


def test_domestic_engine_recipient_type_mismatch():
    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.recipient_type,
                        value="company",
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(
        rule,
        {"entity_type": "individual"},
        effective_date=date(2024, 1, 1),
    )

    assert result.eligible is False
    assert result.requires_review is True


def test_domestic_engine_pe_connection_false():
    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.permanent_establishment_connection,
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(
        rule,
        {"permanent_establishment": False},
        effective_date=date(2024, 1, 1),
    )

    assert result.eligible is False
    assert result.requires_review is True


def test_domestic_engine_unsupported_condition():
    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(condition_type=None)
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.eligible is False
    assert result.requires_review is True
    assert "Unsupported domestic condition type" in result.explanation


def test_domestic_engine_shared_condition_requires_review(monkeypatch):
    import taxtreat.engine.domestic_law_engine as domestic_module

    monkeypatch.setattr(
        domestic_module,
        "_evaluate_condition",
        lambda condition, facts: (False, None, True),
    )

    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator="unsupported",
                        value="10",
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {"ownership": 20}, effective_date=date(2024, 1, 1))

    assert result.eligible is False
    assert result.requires_review is True
    assert "Unsupported domestic condition type" in result.explanation


def test_domestic_engine_shared_condition_is_not_satisfied(monkeypatch):
    import taxtreat.engine.domestic_law_engine as domestic_module

    monkeypatch.setattr(
        domestic_module,
        "_evaluate_condition",
        lambda condition, facts: (False, None, False),
    )

    engine = DomesticLawEngine()
    rule = Rule(
        article=1,
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                    )
                ],
            )
        ],
    )

    result = engine.evaluate(rule, {"ownership": 5}, effective_date=date(2024, 1, 1))

    assert result.eligible is False
    assert result.requires_review is True


def test_domestic_engine_applies_rate_with_source_paragraph():
    engine = DomesticLawEngine()
    rate = WHTRate(rate=12.0, source_paragraph="1")
    rule = Rule(article=1, rates=[rate])

    assert engine._applies_to_date(rate, date(2024, 1, 1)) is True

    result = engine.evaluate(rule, {}, effective_date=date(2024, 1, 1))

    assert result.eligible is True
    assert result.rate == 12.0
