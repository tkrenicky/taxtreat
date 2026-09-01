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
    OUTSIDE_SUBJECT_OF_TAX = "outside_subject_of_tax"


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


_PENDING_SEMANTIC_REMEDIATION_SCOPES: set[tuple[str, str]] = set()


_UI_ROYALTY_CATEGORY_GROUPS = {
    # Current fail-closed UI taxonomy. Each value is intentionally atomic
    # enough to distinguish treaty branches that carry different rates.
    "copyright_literary_artistic_scientific_nonfilm_nonsoftware": {
        "copyright_nonfilm"
    },
    "cinematographic_films_or_broadcast_media": {"film_broadcast"},
    "computer_software": {"software"},
    "patent_trademark_design_model_plan_secret_formula_process_or_knowhow": {
        "industrial_ip"
    },
    "financial_lease_of_equipment": {"equipment_financial"},
    "operating_lease_or_other_use_of_equipment": {"equipment_operating"},
    "other": {"other"},
    # Backward compatibility with older browser payloads. These broad values
    # can legitimately touch more than one treaty branch; the decision engine
    # therefore also contains a duplicate-outcome fail-closed guard below.
    "copyright_literary_artistic_or_scientific": {"copyright_nonfilm"},
    "software_patent_trademark_design_model_plan_secret_formula_process_knowhow": {
        "software",
        "industrial_ip",
    },
    "software_patent_trademark_design_model_plan_secret_formula_process_knowhow_or_industrial_commercial_scientific_equipment": {
        "software",
        "industrial_ip",
        "equipment_financial",
        "equipment_operating",
    },
    "industrial_commercial_or_scientific_equipment": {
        "equipment_financial",
        "equipment_operating",
    },
}


def _royalty_category_groups(value: Any) -> set[str]:
    """Map UI and treaty royalty taxonomies to precise atomic groups.

    Stage 6 treaty projections encode treaty-specific distinctions in the
    category string, including phrases such as ``excluding_computer_software``
    or separate financial/operating lease branches. Token-only fuzzy matching
    used to ignore those exclusions and could make two different treaty rates
    applicable to the same UI selection. This parser keeps the relevant
    distinctions and treats generic equipment as covering both lease forms.
    """

    if value is None:
        return set()

    normalized = str(value).strip().lower()

    if normalized in _UI_ROYALTY_CATEGORY_GROUPS:
        return set(_UI_ROYALTY_CATEGORY_GROUPS[normalized])

    if normalized in {
        "all_royalties_except_cinematographic_and_broadcast_media",
        "all_royalties_excluding_cinematographic_and_broadcast_media",
    }:
        return {
            "copyright_nonfilm",
            "software",
            "industrial_ip",
            "equipment_financial",
            "equipment_operating",
            "other",
        }

    if normalized in {
        "all_royalties_except_industrial_commercial_scientific_equipment",
        "all_royalties_excluding_industrial_commercial_scientific_equipment",
    }:
        return {
            "copyright_nonfilm",
            "film_broadcast",
            "software",
            "industrial_ip",
            "other",
        }

    if normalized == "all_other_article_12_royalties":
        # Generic Article 12 complement used where a non-film copyright
        # branch is carved out separately (e.g. Spain). Film/broadcast and
        # equipment therefore remain in the complement. Treaties whose
        # complement excludes equipment must use the explicit equipment-
        # exclusion category instead of this generic value.
        return {
            "film_broadcast",
            "software",
            "industrial_ip",
            "equipment_financial",
            "equipment_operating",
            "other",
        }

    groups: set[str] = set()

    excludes_software = any(
        marker in normalized
        for marker in (
            "excluding_computer_program",
            "excluding_computer_software",
            "excluding_software",
        )
    )
    excludes_film = any(
        marker in normalized
        for marker in (
            "excluding_cinematographic",
            "excluding_film",
            "excluding_films",
            "excluding_broadcast",
        )
    )

    copyright_nonfilm_tokens = (
        "literary",
        "artistic",
        "dramatic",
        "musical",
        "cultural",
    )
    if any(token in normalized for token in copyright_nonfilm_tokens):
        groups.add("copyright_nonfilm")
    elif normalized in {"copyright", "copyright_royalties"}:
        groups.update({"copyright_nonfilm", "film_broadcast"})

    film_tokens = (
        "cinematographic",
        "film",
        "broadcast_media",
        "broadcast_recording",
        "television",
        "radio",
    )
    if not excludes_film and any(token in normalized for token in film_tokens):
        groups.add("film_broadcast")

    software_tokens = (
        "software",
        "computer_program",
        "computer_software",
    )
    if not excludes_software and any(token in normalized for token in software_tokens):
        groups.add("software")

    industrial_ip_tokens = (
        "patent",
        "trademark",
        "design",
        "model",
        "secret_formula",
        "process",
        "knowhow",
        "know-how",
        "similar_right",
        "technical_assistance",
        "technical_or_economic_studies",
    )
    if any(token in normalized for token in industrial_ip_tokens):
        groups.add("industrial_ip")

    if "financial_lease" in normalized:
        groups.add("equipment_financial")
    if "operating_lease" in normalized:
        groups.add("equipment_operating")
    if (
        "equipment" in normalized
        and "financial_lease" not in normalized
        and "operating_lease" not in normalized
    ):
        groups.update({"equipment_financial", "equipment_operating"})

    if normalized.startswith("all_other_"):
        groups.update(
            {
                "copyright_nonfilm",
                "film_broadcast",
                "software",
                "industrial_ip",
                "other",
            }
        )

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
    """Match one UI royalty class to a treaty-specific category safely."""

    if left == right:
        return True

    left_groups = _royalty_category_groups(left)
    right_groups = _royalty_category_groups(right)

    return bool(
        left_groups
        and right_groups
        and left_groups.intersection(right_groups)
    )


def _rule_condition_signature(rule: LegalRule) -> tuple[Any, ...]:
    """Return the exact projected applicability signature for one rule."""

    return tuple(
        sorted(
            (
                condition.fact,
                condition.fact_source,
                condition.operator,
                repr(condition.value),
            )
            for condition in rule.conditions
        )
    )


def _matching_rule_conflicts(rules: list[LegalRule]) -> list[list[LegalRule]]:
    """Find identical legal branches that project different outcomes.

    Priority is not a safe tie-breaker when two verified rules have the same
    scope, legal layer, effective period and exact conditions but different
    rates/treatments. Such a package is internally ambiguous and must fail
    closed instead of silently selecting the numerically or ordinally preferred
    rule.
    """

    grouped: dict[tuple[Any, ...], list[LegalRule]] = {}
    for rule in rules:
        if rule.effect != "rate":
            continue
        key = (
            rule.source_country,
            rule.recipient_country,
            rule.income_type,
            rule.legal_layer,
            str(rule.article),
            rule.effective_from,
            rule.effective_to,
            _rule_condition_signature(rule),
        )
        grouped.setdefault(key, []).append(rule)

    conflicts: list[list[LegalRule]] = []
    for candidates in grouped.values():
        outcomes = {
            (rule.rate, resolve_tax_treatment(rule))
            for rule in candidates
        }
        if len(outcomes) > 1:
            conflicts.append(sorted(candidates, key=lambda item: item.rule_id))
    return conflicts


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
        condition.fact == "beneficial_owner"
        and condition.operator in {"==", "!="}
        and isinstance(condition_value, str)
        and _boolean_like(condition_value) is None
    ):
        # Legacy Stage 6 projection defect: some public-body/entity
        # classifications were encoded under beneficial_owner. A boolean
        # browser value must not silently disprove such a narrower legal
        # classification and release a general fallback as FINAL.
        return None, condition.fact

    if (
        condition.fact == "recipient_entity_type"
        and condition.operator in {"==", "!="}
        and isinstance(fact_value, str)
        and isinstance(condition_value, str)
    ):
        # Browser/profile entity types are intentionally coarse. A generic
        # value such as "company" cannot safely disprove a treaty branch that
        # requires a narrower legal status (for example
        # "company_other_than_partnership", a bank, central bank, government
        # body, or a wholly government-owned financial institution). Treat
        # that comparison as unresolved so a general fallback cannot become
        # FINAL merely because the UI taxonomy is less granular than the
        # treaty taxonomy.
        coarse_entity_types = {"company", "individual", "fund", "other"}
        if (
            fact_value in coarse_entity_types
            and condition_value not in coarse_entity_types
        ):
            return None, condition.fact

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

    semantic_scope = (
        str(facts.get("recipient_country", "")).upper(),
        str(facts.get("income_type", "")),
    )
    if (
        str(facts.get("source_country", "")).upper() == "CZ"
        and semantic_scope in _PENDING_SEMANTIC_REMEDIATION_SCOPES
    ):
        result.status = DecisionStatus.REVIEW_REQUIRED
        result.requires_review = True
        result.explanation.append(
            "This treaty scope is quarantined pending a source-backed "
            "semantic reprojection and new hash-bound legal approval."
        )
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

    if facts.get("income_type") == "royalty" and facts.get("royalty_category"):
        category_rules = [
            rule
            for rule in relevant_rules
            if rule.legal_layer in {"treaty", "protocol", "mli"}
            and any(
                condition.fact == "royalty_category"
                and condition.operator == "=="
                for condition in rule.conditions
            )
        ]
        if category_rules:
            category_covered = any(
                _royalty_categories_match(
                    facts.get("royalty_category"),
                    condition.value,
                )
                for rule in category_rules
                for condition in rule.conditions
                if condition.fact == "royalty_category"
                and condition.operator == "=="
            )
            if not category_covered:
                result.requires_review = True
                result.missing_facts = ["royalty_category"]
                result.explanation.append(
                    "The selected royalty category is not covered by any "
                    "structured treaty royalty branch for this jurisdiction. "
                    "Treaty classification requires review."
                )
                return result

    if matching_rules:
        # A legacy/broad royalty UI value may semantically match more than one
        # treaty category. Priority is not a legal tie-breaker in that case:
        # if those matched treaty branches produce different outcomes, the
        # transaction classification is insufficient and must fail closed.
        if facts.get("income_type") == "royalty":
            royalty_matches = []
            for rule in matching_rules:
                if rule.legal_layer not in {"treaty", "protocol", "mli"}:
                    continue
                category_conditions = [
                    condition
                    for condition in rule.conditions
                    if condition.fact == "royalty_category"
                    and condition.operator == "=="
                ]
                if category_conditions:
                    royalty_matches.append(rule)

            royalty_outcomes = {
                (rule.rate, resolve_tax_treatment(rule))
                for rule in royalty_matches
            }
            if len(royalty_matches) > 1 and len(royalty_outcomes) > 1:
                result.requires_review = True
                result.missing_facts = ["royalty_category"]
                result.explanation.append(
                    "The supplied royalty classification matches multiple "
                    "treaty branches with different outcomes. A more precise "
                    "royalty category is required."
                )
                return result

        conflicts = _matching_rule_conflicts(matching_rules)
        if conflicts:
            result.requires_review = True
            result.explanation.append(
                "Conflicting verified legal-rule projections have identical "
                "applicability conditions but different outcomes: "
                + "; ".join(
                    ", ".join(rule.rule_id for rule in conflict)
                    for conflict in conflicts
                )
                + "."
            )
            return result

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
