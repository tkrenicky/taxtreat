from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class LegalCondition:
    fact: str
    operator: str
    value: Any


@dataclass
class LegalRule:
    rule_id: str
    income_type: str
    source_country: str
    recipient_country: str
    legal_instrument: str
    article: int | None = None
    paragraph: str | None = None
    rate: float | None = None
    priority: int = 100
    conditions: list[LegalCondition] = field(default_factory=list)
    effect: str = "rate"
    effective_from: date | None = None
    effective_to: date | None = None
    overrides_rule_id: str | None = None
    verification_status: str = "needs_review"
    source_text: str | None = None


@dataclass
class LegalDecisionResult:
    rate: float | None = None
    selected_rule_id: str | None = None
    overridden_rule_id: str | None = None
    eligible: bool = False
    requires_review: bool = False
    missing_facts: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)


_SUPPORTED_OPERATORS = {
    "==": lambda left, right: left == right,
    "!=": lambda left, right: left != right,
    ">=": lambda left, right: left >= right,
    ">": lambda left, right: left > right,
    "<=": lambda left, right: left <= right,
    "<": lambda left, right: left < right,
    "in": lambda left, right: left in right,
    "not in": lambda left, right: left not in right,
}


def _is_effective(rule: LegalRule, as_of: date) -> bool:
    if rule.effective_from is not None and rule.effective_from > as_of:
        return False
    if rule.effective_to is not None and rule.effective_to < as_of:
        return False
    return True


def _matches_scope(rule: LegalRule, facts: dict[str, Any]) -> bool:
    expected = {
        "income_type": rule.income_type,
        "source_country": rule.source_country,
        "recipient_country": rule.recipient_country,
    }

    for name, value in expected.items():
        supplied = facts.get(name)
        if supplied is not None and supplied != value:
            return False

    return True


def _evaluate_condition(
    condition: LegalCondition,
    facts: dict[str, Any],
) -> tuple[bool | None, str | None]:
    if condition.fact not in facts or facts[condition.fact] is None:
        return None, condition.fact

    operator = _SUPPORTED_OPERATORS.get(condition.operator)
    if operator is None:
        raise ValueError(
            f"Unsupported legal-rule operator: {condition.operator!r}"
        )

    try:
        return bool(operator(facts[condition.fact], condition.value)), None
    except TypeError:
        return False, None


def _evaluate_rule(
    rule: LegalRule,
    facts: dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    missing: list[str] = []
    failed: list[str] = []

    for condition in rule.conditions:
        satisfied, missing_fact = _evaluate_condition(condition, facts)

        if missing_fact is not None:
            missing.append(missing_fact)
        elif satisfied is False:
            failed.append(condition.fact)

    matches = not missing and not failed
    return matches, sorted(set(missing)), sorted(set(failed))


def evaluate_legal_rules(
    rules: list[LegalRule],
    facts: dict[str, Any],
    *,
    as_of: date | None = None,
) -> LegalDecisionResult:
    result = LegalDecisionResult()
    evaluation_date = as_of or date.today()

    required_scope_facts = (
        "income_type",
        "source_country",
        "recipient_country",
    )
    missing_scope_facts = [
        fact for fact in required_scope_facts
        if facts.get(fact) in (None, "")
    ]

    if missing_scope_facts:
        result.requires_review = True
        result.missing_facts = missing_scope_facts
        result.explanation.append("The transaction scope is incomplete.")
        return result

    relevant_rules = [
        rule
        for rule in rules
        if _matches_scope(rule, facts)
        and _is_effective(rule, evaluation_date)
    ]

    if not relevant_rules:
        result.requires_review = True
        result.explanation.append(
            "No effective legal rule matches the transaction scope."
        )
        return result

    relevant_rule_ids = {rule.rule_id for rule in relevant_rules}
    broken_overrides = sorted(
        rule.rule_id
        for rule in relevant_rules
        if rule.overrides_rule_id is not None
        and rule.overrides_rule_id not in relevant_rule_ids
    )
    if broken_overrides:
        result.requires_review = True
        result.explanation.append(
            "Legal rules reference missing overridden rules: "
            + ", ".join(broken_overrides)
        )
        return result

    relevant_rule_ids = {rule.rule_id for rule in relevant_rules}
    broken_overrides = sorted(
        rule.rule_id
        for rule in relevant_rules
        if rule.overrides_rule_id is not None
        and rule.overrides_rule_id not in relevant_rule_ids
    )
    if broken_overrides:
        result.requires_review = True
        result.explanation.append(
            "Legal rules reference missing overridden rules: "
            + ", ".join(broken_overrides)
        )
        return result

    unsupported_operators = sorted(
        {
            condition.operator
            for rule in relevant_rules
            for condition in rule.conditions
            if condition.operator not in _SUPPORTED_OPERATORS
        }
    )
    if unsupported_operators:
        result.requires_review = True
        result.explanation.append(
            "Unsupported legal-rule operators: "
            + ", ".join(unsupported_operators)
        )
        return result

    evaluated: list[
        tuple[LegalRule, bool, list[str], list[str]]
    ] = []

    for rule in relevant_rules:
        matches, missing, failed = _evaluate_rule(rule, facts)
        evaluated.append((rule, matches, missing, failed))

    matching_rules = [
        rule
        for rule, matches, _, _ in evaluated
        if matches
    ]
    matching_rules.sort(key=lambda rule: (rule.priority, rule.rule_id))

    if matching_rules:
        leading_priority = matching_rules[0].priority

        unresolved_higher_or_equal_rules = [
            (rule, missing)
            for rule, matches, missing, failed in evaluated
            if not matches
            and missing
            and not failed
            and rule.priority <= leading_priority
        ]

        if unresolved_higher_or_equal_rules:
            result.requires_review = True
            result.missing_facts = sorted(
                {
                    fact
                    for _, missing in unresolved_higher_or_equal_rules
                    for fact in missing
                }
            )
            result.explanation.append(
                "A higher-priority or equally ranked rule cannot be "
                "evaluated because material facts are missing."
            )
            return result

        unverified_candidates = [
            rule
            for rule in matching_rules
            if rule.priority == leading_priority
            and rule.verification_status != "verified"
        ]
        if unverified_candidates:
            result.requires_review = True
            result.explanation.append(
                "The highest-priority applicable legal rule is not verified."
            )
            return result

        selected = matching_rules[0]

        same_priority = [
            rule
            for rule in matching_rules
            if rule.priority == selected.priority
        ]
        distinct_outcomes = {
            (rule.effect, rule.rate, rule.overrides_rule_id)
            for rule in same_priority
        }

        if len(distinct_outcomes) > 1:
            result.requires_review = True
            result.explanation.append(
                "Multiple equally ranked rules produce different outcomes."
            )
            return result

        result.selected_rule_id = selected.rule_id
        result.overridden_rule_id = selected.overrides_rule_id

        if selected.effect == "exclude":
            result.eligible = False
            result.requires_review = False
            result.explanation.append(
                f"Rule {selected.rule_id} excludes application of the "
                "withholding-tax rate."
            )
            return result

        if selected.effect != "rate":
            result.requires_review = True
            result.explanation.append(
                f"Unsupported legal-rule effect: {selected.effect!r}."
            )
            return result

        if selected.rate is None:
            result.requires_review = True
            result.explanation.append(
                f"Rule {selected.rule_id} has no structured rate."
            )
            return result

        result.rate = selected.rate
        result.eligible = True
        result.requires_review = False
        result.explanation.append(
            f"Selected legal rule {selected.rule_id} with rate "
            f"{selected.rate}."
        )
        return result

    unresolved_rules = [
        (rule, missing)
        for rule, _, missing, failed in evaluated
        if missing and not failed
    ]

    if unresolved_rules:
        result.requires_review = True
        result.missing_facts = sorted(
            {
                fact
                for _, missing in unresolved_rules
                for fact in missing
            }
        )
        result.explanation.append(
            "No rule can be selected until material facts are supplied."
        )
        return result

    result.failed_conditions = sorted(
        {
            fact
            for _, _, _, failed in evaluated
            for fact in failed
        }
    )
    result.explanation.append(
        "No effective legal rule satisfies the supplied facts."
    )
    return result
