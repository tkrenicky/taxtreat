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


def evaluate(rule: Any, facts: dict[str, Any]) -> DecisionResult:
    result = DecisionResult()
    rates = getattr(rule, "rates", None) or []

    if not rates:
        result.explanation.append("No structured rates available")
        result.requires_review = True
        return result

    selected_rate = None
    default_rate = None
    for rate in rates:
        rate_conditions = getattr(rate, "conditions", []) or []
        if not rate_conditions:
            default_rate = rate
            result.explanation.append(
                f"Default rate {getattr(rate, 'rate', None)} available for later selection"
            )
            continue

        condition_results = []
        missing = []
        for condition in rate_conditions:
            condition_type = getattr(condition, "condition_type", None)
            if condition_type == ConditionType.minimum_ownership:
                threshold = facts.get("ownership")
                if threshold is None:
                    missing.append("ownership")
                    condition_results.append(False)
                elif threshold >= 10:
                    condition_results.append(True)
                else:
                    condition_results.append(False)
            elif condition_type == ConditionType.minimum_holding_period:
                holding_months = facts.get("holding_months")
                if holding_months is None:
                    missing.append("holding_months")
                    condition_results.append(False)
                elif holding_months >= 12:
                    condition_results.append(True)
                else:
                    condition_results.append(False)
            elif condition_type == ConditionType.beneficial_owner:
                beneficial_owner = facts.get("beneficial_owner")
                if beneficial_owner is None:
                    missing.append("beneficial_owner")
                    condition_results.append(False)
                elif beneficial_owner is True:
                    condition_results.append(True)
                else:
                    condition_results.append(False)
            else:
                condition_results.append(False)

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
