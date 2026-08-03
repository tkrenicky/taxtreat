from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from taxtreat.engine.decision_engine import _evaluate_condition
from taxtreat.engine.models import ConditionType, Rule, WHTCondition


@dataclass
class DomesticLawResult:
    rate: float | None = None
    eligible: bool = False
    requires_review: bool = False
    exemption_applied: bool = False
    missing_facts: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)


class DomesticLawEngine:
    def evaluate(self, rule: Rule, facts: dict[str, Any], effective_date: date | None = None) -> DomesticLawResult:
        result = DomesticLawResult()

        if not rule.rates:
            result.requires_review = True
            result.explanation.append("No domestic withholding rates available")
            return result

        if effective_date is None:
            result.requires_review = True
            result.missing_facts.append("transaction_date")
            result.explanation.append("A transaction date is required")
            return result

        if getattr(rule, "effective_date", None) is not None and getattr(rule, "effective_date") > effective_date:
            result.requires_review = True
            result.explanation.append("Domestic rule is not effective on the requested date")
            return result

        applicable_rates = []
        for rate in getattr(rule, "rates", []) or []:
            if getattr(rate, "effective_date", None) is not None and getattr(rate, "effective_date") > effective_date:
                continue
            applicable_rates.append(rate)

        if not applicable_rates:
            result.requires_review = True
            result.explanation.append("Domestic rule is not effective on the requested date")
            return result

        if facts.get("exempt") is True:
            result.rate = 0.0
            result.exemption_applied = True
            result.eligible = True
            result.explanation.append("Domestic exemption applied")
            return result

        if getattr(rule, "rate", None) is not None and getattr(rule, "rate", None) == 0:
            result.rate = 0.0
            result.eligible = True
            result.explanation.append("Domestic rule is zero-rated")
            return result

        if getattr(rule, "article", None) is not None and getattr(rule, "article", None) <= 0:
            result.requires_review = True
            result.explanation.append("Domestic rule has invalid article reference")
            return result

        if getattr(rule, "rates", None):
            for rate in rule.rates:
                if not self._applies_to_date(rate, effective_date):
                    continue
                if self._evaluate_conditions(rate.conditions, facts, result):
                    result.rate = rate.rate
                    result.eligible = True
                    result.requires_review = False
                    result.explanation.append("Domestic withholding rule satisfied")
                    return result

        result.requires_review = True
        result.explanation.append("Domestic withholding rule could not be evaluated")
        return result

    def _applies_to_date(self, rate: Any, effective_date: date) -> bool:
        if hasattr(rate, "effective_date") and getattr(rate, "effective_date", None) is not None:
            return getattr(rate, "effective_date") <= effective_date
        if hasattr(rate, "source_paragraph") and getattr(rate, "source_paragraph", None) is not None:
            return True
        return True

    def _evaluate_conditions(self, conditions: list[WHTCondition], facts: dict[str, Any], result: DomesticLawResult) -> bool:
        if not conditions:
            return True

        for condition in conditions:
            condition_type = getattr(condition, "condition_type", None)
            if condition_type in {
                ConditionType.minimum_ownership,
                ConditionType.minimum_holding_period,
                ConditionType.beneficial_owner,
                ConditionType.voting_rights,
            }:
                condition_result, missing_fact, condition_review_required = _evaluate_condition(condition, facts)
                if condition_review_required:
                    result.requires_review = True
                    result.explanation.append("Unsupported domestic condition type")
                    return False
                if missing_fact is not None:
                    result.missing_facts.append(missing_fact)
                    return False
                if condition_result is not True:
                    return False
                continue

            if condition_type == ConditionType.recipient_type:
                entity_type = facts.get("entity_type")
                if entity_type is None:
                    result.missing_facts.append("entity_type")
                    return False
                if str(entity_type).lower() != str(condition.value).lower():
                    return False
            elif condition_type == ConditionType.permanent_establishment_connection:
                pe_present = facts.get("permanent_establishment")
                if pe_present is None:
                    result.missing_facts.append("permanent_establishment")
                    return False
                if bool(pe_present) is not True:
                    return False
            else:
                result.requires_review = True
                result.explanation.append("Unsupported domestic condition type")
                return False

        return True
