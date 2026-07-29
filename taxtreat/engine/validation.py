from dataclasses import dataclass, field
from typing import Sequence

from taxtreat.engine.models import ConditionType, Rule, WHTCondition


@dataclass
class ValidationResult:
    passed: bool = False
    score: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class RuleValidator:
    def __init__(self) -> None:
        self.valid_transaction_types = {"dividend", "interest", "royalty"}

    def validate(self, rules: Sequence[Rule]) -> ValidationResult:
        result = ValidationResult()
        if not rules:
            result.errors.append("No rules provided")
            return result

        seen_rates: dict[float, int] = {}
        article_rates: dict[tuple[int | None, str | None], list[float]] = {}

        for rule in rules:
            if rule.transaction_type not in self.valid_transaction_types:
                continue

            if rule.rate is not None:
                seen_rates[rule.rate] = seen_rates.get(rule.rate, 0) + 1
                article_key = (rule.article, rule.transaction_type)
                article_rates.setdefault(article_key, []).append(rule.rate)

            self._validate_rule(rule, result)

        for rate, count in seen_rates.items():
            if count > 1:
                result.warnings.append(f"Duplicate rate detected: {rate}")

        for (article, transaction_type), rates in article_rates.items():
            unique_rates = sorted(set(rates))
            if len(unique_rates) > 1:
                result.warnings.append(
                    f"Multiple rates detected for article {article} ({transaction_type}): {', '.join(str(rate) for rate in unique_rates)}"
                )

        result.passed = not result.errors
        result.score = self._score(result)
        return result

    def _validate_rule(self, rule: Rule, result: ValidationResult) -> None:
        if rule.rate is None:
            result.errors.append(f"Rule for article {rule.article} is missing a rate")
        elif rule.extraction_status == "needs_review" and rule.rate is not None:
            result.warnings.append(f"Rule for article {rule.article} has a rate but needs review")

        if not rule.legal_basis:
            result.errors.append(f"Rule for article {rule.article} is missing legal basis")

        if not rule.source_text:
            result.errors.append(f"Rule for article {rule.article} is missing source text")

        if not rule.paragraph:
            result.warnings.append(f"Rule for article {rule.article} does not reference a source paragraph")

        for condition in rule.conditions:
            if condition.condition_type in {
                ConditionType.minimum_ownership,
                ConditionType.minimum_holding_period,
            }:
                if not condition.value:
                    result.errors.append(
                        f"Condition {condition.condition_type.value} is missing a numeric value"
                    )
            if condition.condition_type in {
                ConditionType.minimum_ownership,
                ConditionType.minimum_holding_period,
            } and condition.unit is None:
                result.warnings.append(
                    f"Condition {condition.condition_type.value} is missing a unit"
                )

        self._check_status_consistency(rule, result)

    def _check_status_consistency(self, rule: Rule, result: ValidationResult) -> None:
        if rule.extraction_status == "confirmed" and rule.rate is None:
            result.errors.append(f"Rule for article {rule.article} is confirmed without a rate")
        if rule.extraction_status == "incomplete" and rule.rate is not None:
            result.warnings.append(f"Rule for article {rule.article} is marked incomplete but has a rate")

    def _score(self, result: ValidationResult) -> int:
        score = 100
        score -= len(result.errors) * 20
        score -= len(result.warnings) * 5
        return max(0, min(100, score))
