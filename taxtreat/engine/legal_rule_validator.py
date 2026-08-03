from __future__ import annotations

from taxtreat.engine.legal_rule_engine import LegalRule, _SUPPORTED_OPERATORS


_ALLOWED_EFFECTS = {"rate", "exclude"}
_ALLOWED_INCOME_TYPES = {"dividend", "interest", "royalty"}
_ALLOWED_INSTRUMENTS = {"treaty", "protocol", "domestic_law", "eu_directive"}
_ALLOWED_STATUSES = {"verified", "needs_review", "rejected"}


def validate_legal_rules(rules: list[LegalRule]) -> list[str]:
    issues: list[str] = []
    rule_ids = [rule.rule_id for rule in rules]
    rules_by_id = {rule.rule_id: rule for rule in rules}

    for rule_id in sorted(set(rule_ids)):
        if rule_ids.count(rule_id) > 1:
            issues.append(f"Duplicate legal-rule id: {rule_id}")

    for rule in rules:
        prefix = f"Rule {rule.rule_id or '<missing id>'}:"

        if not rule.rule_id:
            issues.append(f"{prefix} rule_id is required.")
        if rule.income_type not in _ALLOWED_INCOME_TYPES:
            issues.append(f"{prefix} unsupported income_type.")
        if not rule.source_country or not rule.recipient_country:
            issues.append(f"{prefix} country scope is incomplete.")
        if rule.legal_instrument not in _ALLOWED_INSTRUMENTS:
            issues.append(f"{prefix} unsupported legal_instrument.")
        if rule.effect not in _ALLOWED_EFFECTS:
            issues.append(f"{prefix} unsupported effect.")
        if rule.verification_status not in _ALLOWED_STATUSES:
            issues.append(f"{prefix} unsupported verification_status.")

        if not isinstance(rule.priority, int) or isinstance(rule.priority, bool):
            issues.append(f"{prefix} priority must be an integer.")
        elif rule.priority < 0:
            issues.append(f"{prefix} priority cannot be negative.")

        if rule.effect == "rate":
            if (
                not isinstance(rule.rate, (int, float))
                or isinstance(rule.rate, bool)
            ):
                issues.append(f"{prefix} rate must be numeric.")
            elif not 0 <= float(rule.rate) <= 100:
                issues.append(f"{prefix} rate must be between 0 and 100.")

        if rule.effect == "exclude" and rule.rate is not None:
            issues.append(f"{prefix} exclusion rule must not contain a rate.")

        if (
            rule.effective_from is not None
            and rule.effective_to is not None
            and rule.effective_to < rule.effective_from
        ):
            issues.append(f"{prefix} effective_to precedes effective_from.")

        for condition in rule.conditions:
            if not condition.fact:
                issues.append(f"{prefix} condition fact is required.")
            if condition.operator not in _SUPPORTED_OPERATORS:
                issues.append(
                    f"{prefix} unsupported condition operator "
                    f"{condition.operator!r}."
                )

        if rule.overrides_rule_id is None:
            continue

        target = rules_by_id.get(rule.overrides_rule_id)
        if target is None:
            issues.append(f"{prefix} overridden rule does not exist.")
            continue

        if rule.overrides_rule_id == rule.rule_id:
            issues.append(f"{prefix} rule cannot override itself.")

        source_scope = (
            rule.income_type,
            rule.source_country,
            rule.recipient_country,
        )
        target_scope = (
            target.income_type,
            target.source_country,
            target.recipient_country,
        )
        if source_scope != target_scope:
            issues.append(f"{prefix} override target has different scope.")

        if rule.priority >= target.priority:
            issues.append(
                f"{prefix} overriding rule must have higher precedence."
            )

    return issues
