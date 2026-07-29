from dataclasses import dataclass, field
from typing import Any

from taxtreat.engine.models import ConditionType


@dataclass
class DecisionResult:
    withholding_rate: float | None = None
    selected_legal_basis: str | None = None
    eligible: bool = False
    requires_review: bool = False
    satisfied_conditions: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)


SUPPORTED_OPERATORS = {
    ">=": lambda left, right: left >= right,
    ">": lambda left, right: left > right,
    "<=": lambda left, right: left <= right,
    "<": lambda left, right: left < right,
    "==": lambda left, right: left == right,
    "!=": lambda left, right: left != right,
}


def _coerce_numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        normalized = stripped.replace("%", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _coerce_boolean(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _normalize_holding_period_months(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    if unit is None:
        return None
    normalized_unit = unit.lower().strip()
    if normalized_unit in {"month", "months"}:
        return value
    if normalized_unit in {"year", "years"}:
        return value * 12
    if normalized_unit in {"day", "days"}:
        return value * 12 / 365
    return None


def _evaluate_condition(condition: Any, facts: dict[str, Any]) -> tuple[bool | None, str | None, bool]:
    condition_type = getattr(condition, "condition_type", None)
    operator = getattr(condition, "operator", None)
    value = getattr(condition, "value", None)
    unit = getattr(condition, "unit", None)

    if condition_type == ConditionType.minimum_ownership:
        raw_value = facts.get("ownership")
        if raw_value is None:
            return False, "ownership", False
        numeric_fact_value = _coerce_numeric(raw_value)
        if numeric_fact_value is None:
            return False, None, True
        numeric_condition_value = _coerce_numeric(value)
        if numeric_condition_value is None or operator not in SUPPORTED_OPERATORS:
            return False, None, True
        return SUPPORTED_OPERATORS[operator](numeric_fact_value, numeric_condition_value), None, False

    if condition_type == ConditionType.minimum_holding_period:
        raw_value = facts.get("holding_months")
        if raw_value is None:
            return False, "holding_months", False
        numeric_fact_value = _coerce_numeric(raw_value)
        if numeric_fact_value is None:
            return False, None, True
        numeric_condition_value = _coerce_numeric(value)
        if numeric_condition_value is None or operator not in SUPPORTED_OPERATORS:
            return False, None, True
        normalized_months = _normalize_holding_period_months(numeric_condition_value, unit)
        if normalized_months is None:
            return False, None, True
        return SUPPORTED_OPERATORS[operator](numeric_fact_value, normalized_months), None, False

    if condition_type == ConditionType.beneficial_owner:
        raw_value = facts.get("beneficial_owner")
        if raw_value is None:
            return False, "beneficial_owner", False
        boolean_fact_value = _coerce_boolean(raw_value)
        boolean_condition_value = _coerce_boolean(value)
        if boolean_fact_value is None or boolean_condition_value is None:
            return False, None, True
        if operator not in {"==", "!="}:
            return False, None, True
        return SUPPORTED_OPERATORS[operator](boolean_fact_value, boolean_condition_value), None, False

    return False, None, True


def evaluate(rule: Any, facts: dict[str, Any]) -> DecisionResult:
    result = DecisionResult()
    rates = getattr(rule, "rates", None) or []

    if not rates:
        result.explanation.append("No structured rates available")
        result.requires_review = True
        return result

    selected_rate = None
    default_rate = None
    evaluated_rate = False
    for rate in rates:
        rate_conditions = getattr(rate, "conditions", []) or []
        if not rate_conditions:
            default_rate = rate
            result.explanation.append(
                f"Default rate {getattr(rate, 'rate', None)} available for later selection"
            )
            continue

        evaluated_rate = True
        condition_results = []
        missing = []
        review_required = False
        for condition in rate_conditions:
            condition_result, missing_fact, condition_review_required = _evaluate_condition(condition, facts)
            if condition_review_required:
                review_required = True
                condition_results.append(False)
                continue
            if missing_fact is not None:
                missing.append(missing_fact)
                condition_results.append(False)
            else:
                condition_results.append(condition_result)

        if review_required:
            result.requires_review = True
            result.explanation.append(
                f"Rate {getattr(rate, 'rate', None)} could not be evaluated due to unsupported or invalid conditions"
            )
            continue

        if missing:
            result.missing_facts.extend(missing)
            result.explanation.append(
                f"Rate {getattr(rate, 'rate', None)} could not be evaluated due to missing facts"
            )
            continue

        if all(condition_results):
            selected_rate = rate
            break

        result.explanation.append(
            f"Rate {getattr(rate, 'rate', None)} conditions were not satisfied"
        )

    if selected_rate is None:
        if result.requires_review:
            result.eligible = False
            result.explanation.append("No rate could be selected unambiguously")
            return result
        if default_rate is not None:
            selected_rate = default_rate
            result.explanation.append(
                f"Selected default rate {getattr(default_rate, 'rate', None)}"
            )
        else:
            result.eligible = False
            result.requires_review = True
            result.explanation.append("No rate could be selected unambiguously")
            return result

    result.withholding_rate = getattr(selected_rate, "rate", None)
    result.selected_legal_basis = getattr(selected_rate, "legal_basis", None)
    result.eligible = True
    result.requires_review = False
    result.explanation.append(
        f"Selected rate {getattr(selected_rate, 'rate', None)} from priority {getattr(selected_rate, 'priority', 0)}"
    )
    return result
