from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from taxtreat.engine.legal_facts import (
    load_legal_facts,
    resolve_legal_fact_candidates,
)
from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalDecisionResult,
    LegalRule,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.layered_decision import evaluate_layered_rules


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE_DIR = ROOT / "data" / "legal_rules"
DEFAULT_LEGAL_FACT_DIR = ROOT / "data" / "legal_facts"
INCOME_ALIASES = {
    "dividend": "dividend",
    "dividends": "dividend",
    "interest": "interest",
    "royalty": "royalty",
    "royalties": "royalty",
}


@dataclass(frozen=True)
class CanonicalAnalysisRequest:
    source_country: str
    recipient_country: str
    income_type: str
    transaction_date: date
    facts: dict[str, Any] = field(default_factory=dict)
    determinations: dict[str, Any] = field(default_factory=dict)


def load_rule_catalog(rule_dir: str | Path = DEFAULT_RULE_DIR) -> list[LegalRule]:
    catalog: list[LegalRule] = []
    for path in sorted(Path(rule_dir).glob("*.json")):
        catalog.extend(load_legal_rules(path))
    return catalog


def _legal_condition_names(rules: list[LegalRule]) -> set[str]:
    return {
        condition.fact
        for rule in rules
        for condition in rule.conditions
        if condition.fact_source == "legal"
    }


def analyze_transaction(
    request: CanonicalAnalysisRequest,
    *,
    rule_dir: str | Path = DEFAULT_RULE_DIR,
    legal_fact_dir: str | Path = DEFAULT_LEGAL_FACT_DIR,
) -> LegalDecisionResult:
    normalized_income = INCOME_ALIASES.get(request.income_type.lower())
    if normalized_income is None:
        return LegalDecisionResult(
            status=DecisionStatus.OUT_OF_SCOPE,
            requires_review=False,
            explanation=[f"Unsupported income type: {request.income_type!r}."],
        )

    catalog = load_rule_catalog(rule_dir)
    scoped_rules = [
        rule
        for rule in catalog
        if rule.source_country == request.source_country
        and rule.recipient_country == request.recipient_country
        and rule.income_type == normalized_income
    ]
    if not scoped_rules:
        return LegalDecisionResult(
            status=DecisionStatus.OUT_OF_SCOPE,
            requires_review=False,
            explanation=["The requested country-income scope is not supported."],
        )

    legal_condition_names = _legal_condition_names(scoped_rules)
    transaction_facts = {
        key: value
        for key, value in request.facts.items()
        if key not in legal_condition_names
    }
    transaction_facts.update(
        {
            "income_type": normalized_income,
            "source_country": request.source_country,
            "recipient_country": request.recipient_country,
        }
    )

    legal_fact_records = []
    for path in sorted(Path(legal_fact_dir).glob("*.json")):
        legal_fact_records.extend(load_legal_facts(path))
    legal_facts, unresolved_legal_facts = resolve_legal_fact_candidates(
        legal_fact_records,
        country=request.recipient_country,
        as_of=request.transaction_date,
    )

    result = evaluate_layered_rules(
        scoped_rules,
        transaction_facts,
        as_of=request.transaction_date,
        legal_facts=legal_facts,
        determinations=request.determinations,
    )
    selected_path_ids = set(result.applied_rule_ids)
    if result.candidate_rule_id:
        selected_path_ids.add(result.candidate_rule_id)
    required_legal_facts = {
        condition.fact
        for rule in scoped_rules
        if rule.rule_id in selected_path_ids
        for condition in rule.conditions
        if condition.fact_source == "legal"
    }
    unresolved_required = sorted(
        required_legal_facts.intersection(unresolved_legal_facts)
    )
    if unresolved_required:
        result.status = DecisionStatus.REVIEW_REQUIRED
        result.requires_review = True
        result.rate = None
        result.eligible = False
        result.selected_rule_id = None
        result.missing_facts = sorted(
            set(result.missing_facts).union(
                f"legal_fact:{name}" for name in unresolved_required
            )
        )
        result.explanation.append(
            "Required legal facts have not completed provenance and "
            "independent-approval gates."
        )
    return result
