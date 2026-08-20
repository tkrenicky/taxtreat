from __future__ import annotations

from datetime import date
from typing import Any

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalDecisionResult,
    LegalRule,
    TaxTreatment,
    _evaluate_rule,
    _is_effective,
    _matches_scope,
    resolve_tax_treatment,
)


_LAYER_ORDER = {
    "domestic": 0,
    "treaty": 1,
    "protocol": 2,
    "mli": 3,
    "eu_relief": 4,
}

_TREATMENT_ORDER = {
    TaxTreatment.DOMESTIC_EXEMPTION: 0,
    TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION: 1,
    TaxTreatment.TAXABLE_AT_RATE: 2,
    None: 9,
}


def _candidate_sort_key(rule: LegalRule) -> tuple[Any, ...]:
    """Prefer the most favourable outcome and preserve its correct legal basis.

    A Czech domestic exemption is a complete domestic-law outcome.  Where it
    produces the same numerical result as treaty-exclusive taxation (normally
    both are represented by a zero rate), the exemption must remain the
    selected legal basis rather than being displaced by the treaty layer.
    """

    return (
        float(rule.rate) if rule.rate is not None else float("inf"),
        _TREATMENT_ORDER.get(resolve_tax_treatment(rule), 9),
        -_LAYER_ORDER.get(rule.legal_layer, 99),
        rule.priority,
        rule.rule_id,
    )


def _normalize_missing(rule: LegalRule, missing: list[str]) -> list[str]:
    determination_names = {
        condition.fact
        for condition in rule.conditions
        if condition.fact_source == "determination"
    }
    return [
        f"determination:{name}" if name in determination_names else name
        for name in missing
    ]


def _citation(rule: LegalRule) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "legal_instrument": rule.legal_instrument,
        "legal_layer": rule.legal_layer,
        "rate": rule.rate,
        "tax_treatment": (
            resolve_tax_treatment(rule).value
            if resolve_tax_treatment(rule) is not None
            else None
        ),
        "source_id": rule.source_id,
        "source_url": rule.source_url,
        "article": str(rule.article) if rule.article is not None else None,
        "paragraph": rule.paragraph,
        "excerpt": rule.source_text,
        "excerpt_sha256": rule.source_excerpt_hash,
        "conditions": [
            {
                "fact": condition.fact,
                "operator": condition.operator,
                "value": condition.value,
                "fact_source": condition.fact_source,
            }
            for condition in rule.conditions
        ],
    }


def _layer_result(
    rule: LegalRule,
    *,
    outcome: str,
    missing: list[str] | None = None,
    failed: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "layer": rule.legal_layer,
        "rule_id": rule.rule_id,
        "effect": rule.effect,
        "rate": rule.rate,
        "tax_treatment": (
            resolve_tax_treatment(rule).value
            if resolve_tax_treatment(rule) is not None
            else None
        ),
        "outcome": outcome,
        "verification_status": rule.verification_status,
        "missing_facts": missing or [],
        "failed_conditions": failed or [],
    }


def evaluate_layered_rules(
    rules: list[LegalRule],
    facts: dict[str, Any],
    *,
    as_of: date,
    legal_facts: dict[str, Any] | None = None,
    determinations: dict[str, Any] | None = None,
) -> LegalDecisionResult:
    """Evaluate domestic, treaty/protocol, MLI and EU relief in fixed layers.

    ``candidate_rate`` is intentionally separate from ``rate``.  A candidate
    may be shown for professional review, while ``rate`` is populated only
    when every selected rule and mandatory gate is verified.
    """

    result = LegalDecisionResult()
    legal_facts = legal_facts or {}
    determinations = determinations or {}
    evaluation_facts = dict(facts)
    evaluation_facts.update(determinations)

    relevant = [
        rule
        for rule in rules
        if _matches_scope(rule, facts) and _is_effective(rule, as_of)
    ]
    if not relevant:
        result.status = DecisionStatus.OUT_OF_SCOPE
        result.requires_review = False
        result.explanation.append(
            "No effective legal rule matches the transaction scope."
        )
        return result

    releases = sorted(
        {rule.dataset_release for rule in relevant if rule.dataset_release}
    )
    if len(releases) == 1:
        result.dataset_release = releases[0]
    elif len(releases) > 1:
        result.explanation.append(
            "Relevant legal rules come from inconsistent dataset releases."
        )
        return result

    blocked_layers: set[str] = set()
    mandatory_gate_rules: list[LegalRule] = []
    gate_review_required = False
    missing_material: set[str] = set()

    gate_rules = [rule for rule in relevant if rule.effect == "eligibility_gate"]
    for rule in sorted(gate_rules, key=lambda item: item.rule_id):
        matches, missing, failed = _evaluate_rule(
            rule,
            evaluation_facts,
            legal_facts,
        )
        mandatory_gate_rules.append(rule)
        if matches:
            result.layer_results.append(
                _layer_result(rule, outcome="passed")
            )
            if rule.verification_status != "verified":
                gate_review_required = True
        elif missing:
            normalized_missing = _normalize_missing(rule, missing)
            missing_material.update(normalized_missing)
            blocked_layers.update(rule.applies_to_layers)
            result.layer_results.append(
                _layer_result(
                    rule,
                    outcome="unresolved",
                    missing=normalized_missing,
                )
            )
        else:
            blocked_layers.update(rule.applies_to_layers)
            result.failed_conditions.extend(failed)
            result.layer_results.append(
                _layer_result(rule, outcome="failed", failed=failed)
            )

    evaluated_rates: list[tuple[LegalRule, bool, list[str], list[str]]] = []
    for rule in relevant:
        if rule.effect != "rate":
            continue
        matches, missing, failed = _evaluate_rule(
            rule,
            evaluation_facts,
            legal_facts,
        )
        if rule.legal_layer in blocked_layers:
            matches = False
            failed = sorted(set(failed).union({"eligibility_gate"}))
        normalized_missing = _normalize_missing(rule, missing)
        evaluated_rates.append((rule, matches, normalized_missing, failed))
        result.layer_results.append(
            _layer_result(
                rule,
                outcome=(
                    "applicable"
                    if matches
                    else "unresolved"
                    if missing and not failed
                    else "not_applicable"
                ),
                missing=normalized_missing if not failed else [],
                failed=failed,
            )
        )

    candidates = [
        rule for rule, matches, _, _ in evaluated_rates if matches
    ]
    candidates.sort(key=_candidate_sort_key)
    if not candidates:
        result.missing_facts = sorted(missing_material)
        result.explanation.append(
            "No complete rate path remains after the mandatory legal gates."
        )
        return result

    selected = candidates[0]
    result.candidate_rate = selected.rate
    result.candidate_tax_treatment = resolve_tax_treatment(selected)
    result.candidate_rule_id = selected.rule_id
    result.applied_rule_ids = [
        rule.rule_id
        for rule in sorted(
            [selected, *mandatory_gate_rules],
            key=lambda item: (
                _LAYER_ORDER.get(item.legal_layer, 99),
                item.priority,
                item.rule_id,
            ),
        )
    ]

    unresolved_better = [
        (rule, missing)
        for rule, matches, missing, failed in evaluated_rates
        if not matches
        and missing
        and not failed
        and rule.rate is not None
        and selected.rate is not None
        and float(rule.rate) < float(selected.rate)
    ]
    for _, missing in unresolved_better:
        missing_material.update(missing)

    citation_rules = {
        rule.rule_id: rule
        for rule in [*candidates, *mandatory_gate_rules]
    }
    result.citations = [
        _citation(citation_rules[rule_id])
        for rule_id in sorted(citation_rules)
    ]
    result.missing_facts = sorted(missing_material)
    selected_path = [selected, *mandatory_gate_rules]
    unverified = sorted(
        rule.rule_id
        for rule in selected_path
        if rule.verification_status != "verified"
    )

    if unverified or gate_review_required or result.missing_facts:
        result.status = DecisionStatus.REVIEW_REQUIRED
        result.requires_review = True
        result.explanation.append(
            f"Candidate rate {selected.rate} was calculated from rule "
            f"{selected.rule_id}, but the result is not releasable."
        )
        if unverified:
            result.explanation.append(
                "Rules awaiting independent approval: " + ", ".join(unverified)
            )
        return result

    result.tax_treatment = resolve_tax_treatment(selected)
    if result.tax_treatment == TaxTreatment.TAXABLE_AT_RATE:
        result.rate = selected.rate
    result.selected_rule_id = selected.rule_id
    result.eligible = True
    result.requires_review = False
    result.status = DecisionStatus.FINAL
    result.explanation.append(
        f"Selected verified rule {selected.rule_id} with treatment "
        f"{result.tax_treatment.value}."
    )
    return result
