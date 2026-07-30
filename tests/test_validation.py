from taxtreat.engine.models import ConditionType, Rule, WHTCondition
from taxtreat.engine.validation import RuleValidator, ValidationResult


def valid_rule(**overrides):
    values = {
        "article": 10,
        "paragraph": "2",
        "transaction_type": "dividend",
        "rate": 5.0,
        "conditions": [],
        "legal_basis": "Article 10(2)",
        "source_text": "The tax shall not exceed 5 per cent.",
        "extraction_status": "confirmed",
    }
    values.update(overrides)
    return Rule(**values)


def test_validate_empty_rule_list():
    result = RuleValidator().validate([])

    assert result.passed is False
    assert result.score == 0
    assert result.errors == ["No rules provided"]
    assert result.warnings == []


def test_invalid_transaction_type_is_ignored():
    rule = Rule(
        article=99,
        transaction_type="capital_gain",
        rate=None,
        legal_basis=None,
        source_text=None,
    )

    result = RuleValidator().validate([rule])

    assert result.passed is True
    assert result.score == 100
    assert result.errors == []
    assert result.warnings == []


def test_duplicate_and_multiple_rates_are_reported():
    rules = [
        valid_rule(rate=5.0),
        valid_rule(paragraph="3", rate=5.0),
        valid_rule(paragraph="4", rate=10.0),
    ]

    result = RuleValidator().validate(rules)

    assert result.passed is True
    assert "Duplicate rate detected: 5.0" in result.warnings
    assert (
        "Multiple rates detected for article 10 (dividend): 5.0, 10.0"
        in result.warnings
    )


def test_missing_required_rule_fields():
    rule = Rule(
        article=11,
        paragraph=None,
        transaction_type="interest",
        rate=None,
        legal_basis=None,
        source_text=None,
        extraction_status="needs_review",
    )

    result = RuleValidator().validate([rule])

    assert result.passed is False
    assert "Rule for article 11 is missing a rate" in result.errors
    assert "Rule for article 11 is missing legal basis" in result.errors
    assert "Rule for article 11 is missing source text" in result.errors
    assert (
        "Rule for article 11 does not reference a source paragraph"
        in result.warnings
    )


def test_rate_present_but_rule_needs_review():
    result = RuleValidator().validate(
        [valid_rule(extraction_status="needs_review")]
    )

    assert result.passed is True
    assert (
        "Rule for article 10 has a rate but needs review"
        in result.warnings
    )
    assert result.score == 95


def test_numeric_conditions_require_value_and_unit():
    rule = valid_rule(
        conditions=[
            WHTCondition(
                condition_type=ConditionType.minimum_ownership,
                value=None,
                unit=None,
            ),
            WHTCondition(
                condition_type=ConditionType.minimum_holding_period,
                value="",
                unit=None,
            ),
        ]
    )

    result = RuleValidator().validate([rule])

    assert result.passed is False
    assert (
        "Condition minimum_ownership is missing a numeric value"
        in result.errors
    )
    assert (
        "Condition minimum_holding_period is missing a numeric value"
        in result.errors
    )
    assert (
        "Condition minimum_ownership is missing a unit"
        in result.warnings
    )
    assert (
        "Condition minimum_holding_period is missing a unit"
        in result.warnings
    )


def test_non_numeric_condition_does_not_require_value_or_unit():
    rule = valid_rule(
        conditions=[
            WHTCondition(
                condition_type=ConditionType.beneficial_owner,
                value=None,
                unit=None,
            )
        ]
    )

    result = RuleValidator().validate([rule])

    assert result.passed is True
    assert result.errors == []
    assert result.warnings == []


def test_confirmed_rule_without_rate_is_inconsistent():
    result = RuleValidator().validate(
        [valid_rule(rate=None, extraction_status="confirmed")]
    )

    assert result.passed is False
    assert "Rule for article 10 is missing a rate" in result.errors
    assert (
        "Rule for article 10 is confirmed without a rate"
        in result.errors
    )


def test_incomplete_rule_with_rate_is_inconsistent():
    result = RuleValidator().validate(
        [valid_rule(extraction_status="incomplete")]
    )

    assert result.passed is True
    assert (
        "Rule for article 10 is marked incomplete but has a rate"
        in result.warnings
    )


def test_score_is_clamped_to_zero():
    result = ValidationResult(
        errors=["error"] * 10,
        warnings=["warning"] * 10,
    )

    assert RuleValidator()._score(result) == 0


def test_score_is_100_without_errors_or_warnings():
    assert RuleValidator()._score(ValidationResult()) == 100
