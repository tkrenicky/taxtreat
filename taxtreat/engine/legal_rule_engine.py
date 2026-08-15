from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class DecisionStatus(str, Enum):
    FINAL = "FINAL"
    CONDITIONAL = "CONDITIONAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class TaxTreatment(str, Enum):
    TAXABLE_AT_RATE = "taxable_at_rate"
    EXCLUSIVE_FOREIGN_TAXATION = "exclusive_foreign_taxation"
    DOMESTIC_EXEMPTION = "domestic_exemption"


@dataclass(frozen=True)
class LegalCondition:
    fact: str
    operator: str
    value: Any
    fact_source: str = "transaction"


@dataclass
class LegalRule:
    rule_id: str
    income_type: str
    source_country: str
    recipient_country: str
    legal_instrument: str
    legal_layer: str = "treaty"
    article: int | None = None
    paragraph: str | None = None
    rate: float | None = None
    priority: int = 100
    conditions: list[LegalCondition] = field(default_factory=list)
    effect: str = "rate"
    tax_treatment: TaxTreatment | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    overrides_rule_id: str | None = None
    verification_status: str = "needs_review"
    source_text: str | None = None
    source_id: str | None = None
    source_url: str | None = None
    source_excerpt_hash: str | None = None
    reviewer_id: str | None = None
    reviewed_at: date | None = None
    approved_by: str | None = None
    approved_at: date | None = None
    verification_authority: str | None = None
    review_package_sha256: str | None = None
    approval_dataset_release: str | None = None
    approval_created_at: date | None = None
    dataset_release: str | None = None
    evidence_source_ids: list[str] = field(default_factory=list)
    applies_to_layers: list[str] = field(default_factory=list)


@dataclass
class LegalDecisionResult:
    status: DecisionStatus = DecisionStatus.REVIEW_REQUIRED
    rate: float | None = None
    selected_rule_id: str | None = None
    candidate_rate: float | None = None
    candidate_rule_id: str | None = None
    tax_treatment: TaxTreatment | None = None
    candidate_tax_treatment: TaxTreatment | None = None
    applied_rule_ids: list[str] = field(default_factory=list)
    overridden_rule_id: str | None = None
    eligible: bool = False
    requires_review: bool = True
    missing_facts: list[str] = field(default_factory=list)
    missing_legal_layers: list[str] = field(default_factory=list)
    failed_conditions: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    layer_results: list[dict[str, Any]] = field(default_factory=list)
    dataset_release: str | None = None


_RULE_CONTROL_FACTS = {
    "fallback_case",
    "source_state_taxation",
    "general_article_11_2_rate",
}


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


def _boolean_like(value: Any) -> bool | None:
    """Normalize boolean values preserved in legacy legal-rule projections."""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False

    return None


_UI_ROYALTY_CATEGORY_GROUPS = {
    "copyright_literary_artistic_or_scientific": {"copyright"},
    "software_patent_trademark_design_model_plan_secret_formula_process_knowhow": {
        "industrial_ip"
    },
    # Backward compatibility with the original Stage 7B frontend value.
    "software_patent_trademark_design_model_plan_secret_formula_process_knowhow_or_industrial_commercial_scientific_equipment": {
        "industrial_ip"
    },
    "industrial_commercial_or_scientific_equipment": {"equipment"},
    "other": {"other"},
}


def _royalty_category_groups(value: Any) -> set[str]:
    """Map UI royalty classes and treaty-specific taxonomy to common groups."""

    if value is None:
        return set()

    normalized = str(value).strip().lower()

    if normalized in _UI_ROYALTY_CATEGORY_GROUPS:
        return set(_UI_ROYALTY_CATEGORY_GROUPS[normalized])

    groups: set[str] = set()

    if normalized == "all_other_article_12_royalties":
        groups.add("other")

    copyright_tokens = (
        "copyright",
        "literary",
        "artistic",
        "dramatic",
        "musical",
        "cultural",
    )
    if any(token in normalized for token in copyright_tokens):
        groups.add("copyright")

    industrial_ip_tokens = (
        "patent",
        "trademark",
        "design",
        "model",
        "secret_formula",
        "process",
        "knowhow",
        "know-how",
        "software",
        "computer_program",
        "computer_software",
        "similar_right",
        "technical_assistance",
        "technical_or_economic_studies",
    )
    if any(token in normalized for token in industrial_ip_tokens):
        groups.add("industrial_ip")

    equipment_tokens = (
        "equipment",
        "financial_lease",
        "operating_lease",
    )
    if any(token in normalized for token in equipment_tokens):
        groups.add("equipment")

    if normalized == "other":
        groups.add("other")

    return groups


def _numeric_like(value: Any) -> float | None:
    """Normalize numeric legal thresholds including legacy string percentages."""

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        normalized = value.strip()

        if normalized.endswith("%"):
            normalized = normalized[:-1].strip()

        try:
            return float(normalized)
        except ValueError:
            return None

    return None


def _royalty_categories_match(left: Any, right: Any) -> bool:
    """Match UI royalty category to the taxonomy used by the treaty rule.

    ``right`` is the catalog / Stage 6 condition value.  Some treaty
    packages use ``other`` (or an equivalent all-other label) as the
    residual Article 12 bucket covering copyright, industrial-property
    rights and other royalties, while equipment remains a separate
    category.
    """

    if left == right:
        return True

    left_groups = _royalty_category_groups(left)

    catalog_value = str(right or "").strip().lower()

    if (
        catalog_value == "other"
        or catalog_value.startswith("all_other_")
    ):
        return bool(
            left_groups.intersection(
                {
                    "copyright",
                    "industrial_ip",
                    "other",
                }
            )
        )

    right_groups = _royalty_category_groups(right)

    return bool(
        left_groups
        and right_groups
        and left_groups.intersection(right_groups)
    )


def resolve_tax_treatment(rule: LegalRule) -> TaxTreatment | None:
    """Return the legal outcome without presenting non-taxation as a 0% rate."""

    if rule.effect != "rate":
        return None
    if rule.tax_treatment is not None:
        return TaxTreatment(rule.tax_treatment)
    if rule.rate == 0 and rule.legal_layer == "eu_relief":
        return TaxTreatment.DOMESTIC_EXEMPTION
    if rule.rate == 0 and rule.legal_layer in {"treaty", "protocol", "mli"}:
        return TaxTreatment.EXCLUSIVE_FOREIGN_TAXATION
    return TaxTreatment.TAXABLE_AT_RATE


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
    legal_facts: dict[str, Any],
) -> tuple[bool | None, str | None]:
    if condition.fact in _RULE_CONTROL_FACTS:
        # These values describe the legal-rule branch itself, not a
        # transaction fact. Rule priority still prevents a fallback/general
        # rule from displacing a matching higher-priority special rule.
        return True, None

    fact_store = legal_facts if condition.fact_source == "legal" else facts
    if condition.fact not in fact_store or fact_store[condition.fact] is None:
        prefix = "legal_fact:" if condition.fact_source == "legal" else ""
        return None, prefix + condition.fact

    operator = _SUPPORTED_OPERATORS.get(condition.operator)
    if operator is None:
        raise ValueError(
            f"Unsupported legal-rule operator: {condition.operator!r}"
        )

    fact_value = fact_store[condition.fact]
    condition_value = condition.value

    if (
        condition.fact == "royalty_category"
        and condition.operator in {"==", "!="}
    ):
        matched = _royalty_categories_match(
            fact_value,
            condition_value,
        )
        if condition.operator == "!=":
            matched = not matched
        return matched, None

    fact_boolean = _boolean_like(fact_value)
    condition_boolean = _boolean_like(condition_value)

    if (
        fact_boolean is not None
        and condition_boolean is not None
        and condition.operator in {"==", "!="}
    ):
        matched = fact_boolean == condition_boolean
        if condition.operator == "!=":
            matched = not matched
        return matched, None

    if condition.operator in {">", ">=", "<", "<="}:
        fact_numeric = _numeric_like(fact_value)
        condition_numeric = _numeric_like(condition_value)

        if (
            fact_numeric is not None
            and condition_numeric is not None
        ):
            return bool(
                operator(
                    fact_numeric,
                    condition_numeric,
                )
            ), None

    try:
        return bool(operator(fact_value, condition_value)), None
    except TypeError:
        return False, None


def _evaluate_rule(
    rule: LegalRule,
    facts: dict[str, Any],
    legal_facts: dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    missing: list[str] = []
    failed: list[str] = []

    for condition in rule.conditions:
        satisfied, missing_fact = _evaluate_condition(
            condition,
            facts,
            legal_facts,
        )

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
    legal_facts: dict[str, Any] | None = None,
) -> LegalDecisionResult:
    result = LegalDecisionResult()
    if as_of is None:
        result.missing_facts = ["transaction_date"]
        result.explanation.append("A transaction date is required.")
        return result
    evaluation_date = as_of
    legal_facts = legal_facts or {}

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
        result.status = DecisionStatus.OUT_OF_SCOPE
        result.requires_review = False
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
        matches, missing, failed = _evaluate_rule(rule, facts, legal_facts)
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
            (
                rule.effect,
                rule.rate,
                resolve_tax_treatment(rule),
                rule.overrides_rule_id,
            )
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
            result.status = DecisionStatus.FINAL
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

        result.tax_treatment = resolve_tax_treatment(selected)
        result.candidate_tax_treatment = result.tax_treatment
        if result.tax_treatment == TaxTreatment.TAXABLE_AT_RATE:
            result.rate = selected.rate
        result.eligible = True
        result.requires_review = False
        result.status = DecisionStatus.FINAL
        result.explanation.append(
            f"Selected legal rule {selected.rule_id} with treatment "
            f"{result.tax_treatment.value}."
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
    result.requires_review = True
    return result
