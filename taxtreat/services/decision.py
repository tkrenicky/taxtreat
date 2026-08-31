from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

from taxtreat.countries.registry import get_country_config
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
from taxtreat.registry.legal_scope import supported_scope_keys
from taxtreat.services.runtime_gate import evaluate_runtime_gate


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULE_DIR = ROOT / "data" / "legal_rules_stage6"
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




def _apply_source_country_release_manifest_gate(
    request: CanonicalAnalysisRequest,
    result: LegalDecisionResult,
    *,
    country_config: Any | None = None,
) -> LegalDecisionResult:
    """Apply an optional country-package production release manifest."""

    if result.status != DecisionStatus.FINAL:
        return result

    if country_config is None:
        try:
            country_config = get_country_config(
                request.source_country
            )
        except KeyError:
            return result

    manifest_path = country_config.release_manifest_path
    if manifest_path is None:
        return result

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        release_eligible = False
        release_status = "manifest_unavailable"
        blockers = [
            "source_country_release_manifest_unavailable"
        ]
    else:
        release_eligible = (
            manifest.get("release_eligible") is True
        )
        release_status = str(
            manifest.get("release_status") or "unknown"
        )
        blockers = list(manifest.get("blockers") or [])

    if release_eligible:
        return result

    if result.candidate_rule_id is None:
        result.candidate_rule_id = result.selected_rule_id

    if result.candidate_tax_treatment is None:
        result.candidate_tax_treatment = result.tax_treatment

    if (
        result.candidate_rate is None
        and result.rate is not None
    ):
        result.candidate_rate = result.rate

    result.status = DecisionStatus.REVIEW_REQUIRED
    result.requires_review = True
    result.eligible = False
    result.rate = None
    result.tax_treatment = None
    result.selected_rule_id = None

    if (
        "source_country_release_manifest"
        not in result.missing_legal_layers
    ):
        result.missing_legal_layers.append(
            "source_country_release_manifest"
        )

    blocker_text = (
        ", ".join(blockers)
        if blockers
        else "release_manifest_not_eligible"
    )

    result.explanation.append(
        f"The {country_config.code} legal result has been "
        "calculated, but the source-country release manifest "
        "is not currently eligible for production "
        f"(status={release_status}; blockers={blocker_text})."
    )

    return result


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

    try:
        country_config = get_country_config(request.source_country)
    except KeyError:
        country_config = None

    if country_config is not None and not country_config.runtime_released:
        return LegalDecisionResult(
            status=DecisionStatus.REVIEW_REQUIRED,
            requires_review=True,
            rate=None,
            eligible=False,
            missing_legal_layers=[
                "domestic",
                "mli",
                "treaty_or_protocol",
            ],
            explanation=[
                f"{country_config.code} source-country package has not been released."
            ],
        )

    domestic_result = None
    if (
        country_config is not None
        and country_config.domestic_precedence_handler is not None
    ):
        domestic_result = country_config.domestic_precedence_handler(
            recipient_country=request.recipient_country,
            income_type=normalized_income,
            transaction_date=request.transaction_date,
            facts=request.facts,
        )

    if domestic_result is not None:
        return _apply_source_country_release_manifest_gate(
            request,
            domestic_result,
            country_config=country_config,
        )

    runtime_gate = evaluate_runtime_gate(
        source_country=request.source_country,
        recipient_country=request.recipient_country,
        income_type=normalized_income,
        transaction_date=request.transaction_date,
        facts=request.facts,
    )

    if (
        runtime_gate.applies
        and not runtime_gate.allowed
    ):
        return LegalDecisionResult(
            status=DecisionStatus.REVIEW_REQUIRED,
            requires_review=True,
            rate=None,
            eligible=False,
            missing_facts=runtime_gate.missing_facts,
            explanation=[
                runtime_gate.explanation
                or (
                    "Transaction-level legal eligibility "
                    "is unresolved."
                )
            ],
        )

    effective_rule_dir = rule_dir
    if (
        country_config is not None
        and Path(rule_dir).resolve() == DEFAULT_RULE_DIR.resolve()
        and country_config.rule_directory is not None
    ):
        effective_rule_dir = country_config.rule_directory

    catalog = load_rule_catalog(effective_rule_dir)
    scoped_rules = [
        rule
        for rule in catalog
        if rule.source_country == request.source_country
        and rule.recipient_country == request.recipient_country
        and rule.income_type == normalized_income
    ]
    try:
        config = get_country_config(request.source_country)
    except KeyError:
        config = None

    if config is not None and config.rule_overlay_handler is not None:
        scoped_rules = config.rule_overlay_handler(
            scoped_rules=scoped_rules,
            income_type=normalized_income,
            transaction_date=request.transaction_date,
        )

    if not scoped_rules:
        scope_key = (
            request.source_country,
            request.recipient_country,
            normalized_income,
        )
        if (
            country_config is not None
            and scope_key in supported_scope_keys(
                source_country=request.source_country
            )
        ):
            return LegalDecisionResult(
                status=DecisionStatus.REVIEW_REQUIRED,
                requires_review=True,
                missing_legal_layers=[
                    "domestic",
                    "eu_relief",
                    "mli",
                    "treaty_or_protocol",
                ],
                explanation=[
                    "The requested scope is registered, but its consolidated "
                    "legal rules have not completed source, effective-date, "
                    "protocol/MLI and independent-approval gates."
                ],
            )
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
        result.tax_treatment = None
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
    return _apply_source_country_release_manifest_gate(
        request,
        result,
        country_config=country_config,
    )
