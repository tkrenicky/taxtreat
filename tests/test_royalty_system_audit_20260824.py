from itertools import combinations
from pathlib import Path

from taxtreat.engine.legal_rule_engine import (
    _evaluate_rule,
    _royalty_categories_match,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules


RULE_DIR = Path("data/legal_rules_stage6")
BOOTSTRAP = Path("app/web/workspace-report-export.js")
CANONICAL_I18N = Path("app/web/workspace-canonical-live-i18n-20260824.js")
VISIBILITY_FIX = Path("app/web/workspace-income-type-visibility-fix-20260824.js")

UI_CATEGORIES = (
    "copyright_literary_artistic_or_scientific",
    "software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "industrial_commercial_or_scientific_equipment",
    "other",
)


def _all_royalty_rules():
    rules = []
    for path in sorted(RULE_DIR.glob("*.json")):
        rules.extend(rule for rule in load_legal_rules(path) if rule.income_type == "royalty")
    return rules


def _category_condition(rule):
    return next((c for c in rule.conditions if c.fact == "royalty_category"), None)


def _ui_matches(rule):
    condition = _category_condition(rule)
    if condition is None:
        return set(UI_CATEGORIES)
    if condition.operator == "==":
        return {ui for ui in UI_CATEGORIES if _royalty_categories_match(ui, condition.value)}
    if condition.operator == "!=":
        return {ui for ui in UI_CATEGORIES if not _royalty_categories_match(ui, condition.value)}
    return set()


def _non_category_signature(rule):
    return tuple(
        sorted(
            (
                condition.fact,
                condition.fact_source,
                condition.operator,
                repr(condition.value),
            )
            for condition in rule.conditions
            if condition.fact != "royalty_category"
        )
    )


def _effective_signature(rule):
    return (rule.effective_from, rule.effective_to)


def _facts_satisfying(rule, royalty_category):
    facts = {
        "income_type": "royalty",
        "source_country": rule.source_country,
        "recipient_country": rule.recipient_country,
    }
    legal_facts = {}
    for condition in rule.conditions:
        target = legal_facts if condition.fact_source == "legal" else facts
        if condition.fact == "royalty_category":
            target[condition.fact] = royalty_category
        elif condition.fact not in {
            "fallback_case",
            "source_state_taxation",
            "general_article_11_2_rate",
        }:
            target[condition.fact] = condition.value
    return facts, legal_facts


def test_income_specific_hidden_state_cannot_be_overridden_by_layout_css():
    script = VISIBILITY_FIX.read_text(encoding="utf-8")
    assert "#dividend-facts[hidden]" in script
    assert "#interest-facts[hidden]" in script
    assert "#royalty-facts[hidden]" in script
    assert "display:none!important" in script
    assert "#interest-facts:not([hidden])" in script
    assert "#royalty-facts:not([hidden])" in script


def test_canonical_live_i18n_is_loaded_after_income_visibility_fix():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    visibility = bootstrap.index("workspace-income-type-visibility-fix-20260824.js")
    canonical = bootstrap.index("workspace-canonical-live-i18n-20260824.js")
    assert canonical > visibility


def test_canonical_live_i18n_has_no_broad_mutation_observer():
    script = CANONICAL_I18N.read_text(encoding="utf-8")
    assert "MutationObserver" not in script
    assert 'select.dispatchEvent(new Event("change", { bubbles: true }))' in script
    assert "Skutečný vlastník příjmu" in script
    assert "Vazba ke stálé provozovně v ČR" in script
    assert "Potvrzení o daňovém rezidentství" in script
    assert "Doplňující údaje pro možné vnitrostátní osvobození" in script


def test_at_copyright_and_industrial_ip_are_distinct_article_12_outcomes():
    rules = {rule.rule_id: rule for rule in load_legal_rules(RULE_DIR / "at.json")}
    copyright_rule = rules["CZ-AT-ROYALTY-CURRENT-1"]
    industrial_rule = rules["CZ-AT-ROYALTY-CURRENT-2"]

    assert copyright_rule.rate == 0.0
    assert industrial_rule.rate == 5.0

    copyright_ui = "copyright_literary_artistic_or_scientific"
    industrial_ui = "software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow"

    facts, legal = _facts_satisfying(copyright_rule, copyright_ui)
    assert _evaluate_rule(copyright_rule, facts, legal)[0] is True
    facts, legal = _facts_satisfying(industrial_rule, copyright_ui)
    assert _evaluate_rule(industrial_rule, facts, legal)[0] is False

    facts, legal = _facts_satisfying(industrial_rule, industrial_ui)
    assert _evaluate_rule(industrial_rule, facts, legal)[0] is True
    facts, legal = _facts_satisfying(copyright_rule, industrial_ui)
    assert _evaluate_rule(copyright_rule, facts, legal)[0] is False


def test_every_verified_royalty_category_rule_maps_to_at_least_one_ui_category():
    unmapped = []
    for rule in _all_royalty_rules():
        if rule.effect != "rate" or rule.verification_status != "verified":
            continue
        condition = _category_condition(rule)
        if condition is not None and not _ui_matches(rule):
            unmapped.append((rule.rule_id, condition.operator, condition.value))
    assert not unmapped, f"Verified royalty rules not reachable from UI taxonomy: {unmapped}"


def test_no_identical_royalty_legal_branch_has_overlapping_ui_category_with_different_rate():
    grouped = {}
    for rule in _all_royalty_rules():
        if rule.effect != "rate" or rule.verification_status != "verified":
            continue
        if rule.legal_layer not in {"treaty", "protocol", "mli"}:
            continue
        key = (
            rule.source_country,
            rule.recipient_country,
            rule.legal_layer,
            str(rule.article),
            _effective_signature(rule),
            _non_category_signature(rule),
        )
        grouped.setdefault(key, []).append(rule)

    conflicts = []
    for key, rules in grouped.items():
        for left, right in combinations(rules, 2):
            if left.rate == right.rate:
                continue
            overlap = sorted(_ui_matches(left).intersection(_ui_matches(right)))
            if overlap:
                conflicts.append(
                    {
                        "scope": key[:4],
                        "left": (left.rule_id, left.rate),
                        "right": (right.rule_id, right.rate),
                        "ui_categories": overlap,
                    }
                )
    assert not conflicts, f"Conflicting royalty branches reachable from the same UI category: {conflicts}"
