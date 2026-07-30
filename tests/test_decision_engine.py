import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from taxtreat.engine.decision_engine import evaluate
from taxtreat.engine.extractors import extract_conditions
from taxtreat.engine.models import ConditionType, Rule, WHTCondition, WHTRate


def build_rule() -> Rule:
    return Rule(
        article=10,
        transaction_type="dividend",
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                        unit="%",
                        description="minimum ownership",
                    )
                ],
                legal_basis="Art 10",
                priority=0,
            ),
            WHTRate(
                rate=15.0,
                conditions=[],
                legal_basis="default",
                priority=1,
            ),
        ],
    )


def test_ownership_condition_uses_operator_and_value():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"ownership": 12})

    assert result.eligible is True
    assert result.withholding_rate == 5.0
    assert result.selected_legal_basis == "Art 10"


def test_holding_period_condition_supports_year_and_day_units():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_holding_period,
                        operator=">=",
                        value="1",
                        unit="year",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(
                rate=10.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_holding_period,
                        operator="==",
                        value="365",
                        unit="day",
                    )
                ],
                legal_basis="Art 10b",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"holding_months": 12})

    assert result.eligible is True
    assert result.withholding_rate == 5.0


def test_beneficial_owner_condition_uses_boolean_value():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="==",
                        value="true",
                        unit=None,
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"beneficial_owner": True})

    assert result.eligible is True
    assert result.withholding_rate == 5.0


@pytest.mark.parametrize(
    ("facts", "expected_rate", "expected_eligible"),
    [
        ({"ownership": 12}, 5.0, True),
        ({"ownership": 8}, 15.0, True),
    ],
)
def test_ownership_threshold_uses_operator_and_value(facts, expected_rate, expected_eligible):
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, facts)

    assert result.eligible is expected_eligible
    assert result.withholding_rate == expected_rate
    assert result.requires_review is False


def test_holding_period_thresholds_support_month_and_year_units():
    month_rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_holding_period,
                        operator=">=",
                        value="12",
                        unit="month",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    year_rule = Rule(
        rates=[
            WHTRate(
                rate=10.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_holding_period,
                        operator=">=",
                        value="2",
                        unit="year",
                    )
                ],
                legal_basis="Art 10b",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    month_result = evaluate(month_rule, {"holding_months": 12})
    assert month_result.eligible is True
    assert month_result.withholding_rate == 5.0

    year_result = evaluate(year_rule, {"holding_months": 24})
    assert year_result.eligible is True
    assert year_result.withholding_rate == 10.0


def test_beneficial_owner_boolean_condition_supports_true_and_false():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="==",
                        value="true",
                        unit=None,
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"beneficial_owner": True})
    assert result.eligible is True
    assert result.withholding_rate == 5.0

    result = evaluate(rule, {"beneficial_owner": False})
    assert result.eligible is True
    assert result.withholding_rate == 15.0


def test_unsupported_operator_requires_review():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator="contains",
                        value="10",
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            )
        ]
    )

    result = evaluate(rule, {"ownership": 12})

    assert result.eligible is False
    assert result.requires_review is True


def test_unsupported_operator_marks_for_review_even_with_default_rate():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator="contains",
                        value="10",
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"ownership": 12})

    assert result.requires_review is True
    assert result.eligible is False
    assert result.withholding_rate is None


def test_extract_conditions_uses_boolean_equality_operator():
    conditions = extract_conditions("Beneficial owner required")

    assert len(conditions) == 1
    assert conditions[0].condition_type == ConditionType.beneficial_owner
    assert conditions[0].operator == "=="


def test_unsupported_unit_requires_review():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_holding_period,
                        operator=">=",
                        value="12",
                        unit="week",
                    )
                ],
                legal_basis="Art 10",
            )
        ]
    )

    result = evaluate(rule, {"holding_months": 12})

    assert result.eligible is False
    assert result.requires_review is True


def test_numeric_condition_values_with_percent_sign_are_parsed():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10%",
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            ),
            WHTRate(rate=15.0, conditions=[], legal_basis="default"),
        ]
    )

    result = evaluate(rule, {"ownership": 12})

    assert result.eligible is True
    assert result.withholding_rate == 5.0


@pytest.mark.parametrize(
    "condition_value",
    ["not-a-number", "", "10x"],
)
def test_invalid_numeric_value_requires_review(condition_value):
    rule = Rule(
        rates=[
            WHTRate(
                rate=5.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value=condition_value,
                        unit="%",
                    )
                ],
                legal_basis="Art 10",
            )
        ]
    )

    result = evaluate(rule, {"ownership": 12})

    assert result.eligible is False
    assert result.requires_review is True


if __name__ == "__main__":
    rule = build_rule()

    scenarios = [
        ("ownership = 25, beneficial_owner = True", {"ownership": 25, "beneficial_owner": True}),
        ("ownership = 5, beneficial_owner = True", {"ownership": 5, "beneficial_owner": True}),
        ("beneficial_owner = True, ownership missing", {"beneficial_owner": True}),
    ]

    for label, facts in scenarios:
        result = evaluate(rule, facts)
        print(f"Scenario: {label}")
        print(f"  withholding_rate={result.withholding_rate}")
        print(f"  eligible={result.eligible}")
        print(f"  requires_review={result.requires_review}")
        print(f"  missing_facts={result.missing_facts}")
        print(f"  explanation={result.explanation}")
        print()

from taxtreat.engine.decision_engine import (
    _coerce_numeric,
    _coerce_boolean,
    _normalize_holding_period_months,
)


def test_coerce_numeric():
    assert _coerce_numeric(10) == 10.0
    assert _coerce_numeric("10%") == 10.0
    assert _coerce_numeric("10,5") == 10.5
    assert _coerce_numeric("") is None
    assert _coerce_numeric(True) is None
    assert _coerce_numeric("abc") is None


def test_coerce_boolean():
    assert _coerce_boolean(True) is True
    assert _coerce_boolean(False) is False
    assert _coerce_boolean("YES") is True
    assert _coerce_boolean("no") is False
    assert _coerce_boolean("x") is None


def test_normalize_holding_period():
    assert _normalize_holding_period_months(12, "month") == 12
    assert _normalize_holding_period_months(2, "year") == 24
    assert round(_normalize_holding_period_months(365, "day"), 2) == 12
    assert _normalize_holding_period_months(1, "week") is None
    assert _normalize_holding_period_months(None, "month") is None
    assert _normalize_holding_period_months(1, None) is None


def test_missing_ownership_fact():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                    )
                ],
            )
        ]
    )

    result = evaluate(rule, {})

    assert result.requires_review
    assert "ownership" in result.missing_facts


def test_no_rates():
    result = evaluate(Rule(rates=[]), {})

    assert result.requires_review
    assert result.eligible is False


def test_only_default_rate():
    result = evaluate(
        Rule(
            rates=[
                WHTRate(rate=15, conditions=[], legal_basis="default")
            ]
        ),
        {},
    )

    assert result.eligible
    assert result.withholding_rate == 15


def test_no_rate_selected():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                    )
                ],
            )
        ]
    )

    result = evaluate(rule, {"ownership": 1})

    assert result.requires_review
    assert result.eligible is False


from taxtreat.engine.decision_engine import (
    _coerce_boolean,
    _coerce_numeric,
    _normalize_holding_period_months,
)


def test_coerce_numeric_edge_cases():
    assert _coerce_numeric(None) is None
    assert _coerce_numeric(True) is None
    assert _coerce_numeric(False) is None
    assert _coerce_numeric("") is None
    assert _coerce_numeric("   ") is None
    assert _coerce_numeric("10%") == 10.0
    assert _coerce_numeric("10,5") == 10.5
    assert _coerce_numeric("abc") is None
    assert _coerce_numeric(object()) is None


def test_coerce_boolean_edge_cases():
    assert _coerce_boolean(True) is True
    assert _coerce_boolean(False) is False
    assert _coerce_boolean("TRUE") is True
    assert _coerce_boolean(" yes ") is True
    assert _coerce_boolean("1") is True
    assert _coerce_boolean("FALSE") is False
    assert _coerce_boolean("no") is False
    assert _coerce_boolean("0") is False
    assert _coerce_boolean("unknown") is None
    assert _coerce_boolean(123) is None


def test_normalize_holding_period_all_units():
    assert _normalize_holding_period_months(12, "month") == 12
    assert _normalize_holding_period_months(12, "months") == 12
    assert _normalize_holding_period_months(1, "year") == 12
    assert _normalize_holding_period_months(2, "years") == 24
    assert _normalize_holding_period_months(365, "day") == 12
    assert _normalize_holding_period_months(730, "days") == 24
    assert _normalize_holding_period_months(None, "months") is None
    assert _normalize_holding_period_months(12, None) is None
    assert _normalize_holding_period_months(12, "weeks") is None


def test_invalid_boolean_condition_requires_review():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="contains",
                        value="true",
                    )
                ],
            )
        ]
    )

    result = evaluate(rule, {"beneficial_owner": True})

    assert result.requires_review is True
    assert result.eligible is False


def test_invalid_boolean_value_requires_review():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="==",
                        value="banana",
                    )
                ],
            )
        ]
    )

    result = evaluate(rule, {"beneficial_owner": True})

    assert result.requires_review is True
    assert result.eligible is False


def test_unknown_condition_type_requires_review():
    class DummyCondition:
        condition_type = object()
        operator = "=="
        value = "1"
        unit = None

    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[DummyCondition()],
            )
        ]
    )

    result = evaluate(rule, {})

    assert result.requires_review is True
    assert result.eligible is False


def test_no_matching_rate_without_default_requires_review():
    rule = Rule(
        rates=[
            WHTRate(
                rate=5,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="50",
                        unit="%",
                    )
                ],
            )
        ]
    )

    result = evaluate(rule, {"ownership": 10})

    assert result.requires_review is True
    assert result.eligible is False
