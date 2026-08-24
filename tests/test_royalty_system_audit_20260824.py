from datetime import date
from itertools import combinations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    _evaluate_rule,
    _royalty_categories_match,
    evaluate_legal_rules,
)
from taxtreat.engine.legal_rule_loader import load_legal_rules
from taxtreat.engine.layered_decision import evaluate_layered_rules


RULE_DIR = REPO_ROOT / "data/legal_rules_stage6"
BOOTSTRAP = REPO_ROOT / "app/web/workspace-report-export.js"
CANONICAL_I18N = REPO_ROOT / "app/web/workspace-canonical-live-i18n-20260824.js"
VISIBILITY_FIX = REPO_ROOT / "app/web/workspace-income-type-visibility-fix-20260824.js"
ROYALTY_UI = REPO_ROOT / "app/web/workspace-royalty-taxonomy-20260824.js"

UI_CATEGORIES = (
    "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    "cinematographic_films_or_broadcast_media",
    "computer_software",
    "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "financial_lease_of_equipment",
    "operating_lease_or_other_use_of_equipment",
    "other",
)


def _all_royalty_rules():
    rules = []
    for path in sorted(RULE_DIR.glob("*.json")):
        rules.extend(rule for rule in load_legal_rules(path) if rule.income_type == "royalty")
    return rules


def _category_condition(rule):
    return next((c for c in rule.conditions if c.fact == "royalty_category"), None)


def _category_value(rule):
    condition = _category_condition(rule)
    if condition is None or condition.operator != "==":
        return None
    return str(condition.value or "").strip().lower()


def _is_residual(rule):
    value = _category_value(rule)
    return bool(value and (value == "other" or value.startswith("all_other_")))


def _ui_matches(rule):
    condition = _category_condition(rule)
    if condition is None:
        return set(UI_CATEGORIES)
    if condition.operator == "==":
        return {ui for ui in UI_CATEGORIES if _royalty_categories_match(ui, condition.value)}
    if condition.operator == "!=":
        return {ui for ui in UI_CATEGORIES if not _royalty_categories_match(ui, condition.value)}
    return set()


def _condition_signature(rule, *, include_category=True):
    return tuple(
        sorted(
            (
                condition.fact,
                condition.fact_source,
                condition.operator,
                repr(condition.value),
            )
            for condition in rule.conditions
            if include_category or condition.fact != "royalty_category"
        )
    )


def _effective_signature(rule):
    return (rule.effective_from, rule.effective_to)


def _facts_satisfying(rule, royalty_category):
    facts = {
        "income_type": "royalty",
        "source_country": rule.source_country,
        "recipient_country": rule.recipient_country,
        "royalty_category": royalty_category,
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


def test_refined_royalty_taxonomy_is_loaded_before_final_i18n_pass():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    visibility = bootstrap.index("workspace-income-type-visibility-fix-20260824.js")
    taxonomy = bootstrap.index("workspace-royalty-taxonomy-20260824.js")
    canonical = bootstrap.index("workspace-canonical-live-i18n-20260824.js")
    assert taxonomy > visibility
    assert canonical > taxonomy


def test_refined_royalty_ui_contains_all_audited_categories():
    script = ROYALTY_UI.read_text(encoding="utf-8")
    for category in UI_CATEGORIES:
        assert category in script
    assert "MutationObserver" not in script


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

    copyright_ui = "copyright_literary_artistic_scientific_nonfilm_nonsoftware"
    industrial_ui = "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"

    facts, legal = _facts_satisfying(copyright_rule, copyright_ui)
    assert _evaluate_rule(copyright_rule, facts, legal)[0] is True
    facts, legal = _facts_satisfying(industrial_rule, copyright_ui)
    assert _evaluate_rule(industrial_rule, facts, legal)[0] is False

    facts, legal = _facts_satisfying(industrial_rule, industrial_ui)
    assert _evaluate_rule(industrial_rule, facts, legal)[0] is True
    facts, legal = _facts_satisfying(copyright_rule, industrial_ui)
    assert _evaluate_rule(copyright_rule, facts, legal)[0] is False


def test_excluding_software_taxonomy_does_not_match_software_ui_category():
    examples = (
        "copyright_literary_artistic_scientific_excluding_computer_program_including_films_and_broadcast_media",
        "copyright_literary_artistic_scientific_excluding_computer_software_including_films_and_broadcast_media",
    )
    for category in examples:
        assert not _royalty_categories_match("computer_software", category)
        assert _royalty_categories_match(
            "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
            category,
        )


def test_every_verified_royalty_category_rule_maps_to_at_least_one_ui_category():
    unmapped = []
    for rule in _all_royalty_rules():
        if rule.effect != "rate" or rule.verification_status != "verified":
            continue
        condition = _category_condition(rule)
        if condition is not None and not _ui_matches(rule):
            unmapped.append((rule.rule_id, condition.operator, condition.value))
    assert not unmapped, f"Verified royalty rules not reachable from UI taxonomy: {unmapped}"


def test_no_mapper_overlap_can_silently_select_different_royalty_rate():
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
            _condition_signature(rule, include_category=False),
        )
        grouped.setdefault(key, []).append(rule)

    unsafe_mapper_conflicts = []
    projection_conflicts = []
    residual_overlaps = []

    for key, rules in grouped.items():
        for left, right in combinations(rules, 2):
            if left.rate == right.rate:
                continue
            overlap = sorted(_ui_matches(left).intersection(_ui_matches(right)))
            if not overlap:
                continue

            item = {
                "scope": key[:4],
                "left": (left.rule_id, left.rate),
                "right": (right.rule_id, right.rate),
                "ui_categories": overlap,
            }
            if _condition_signature(left) == _condition_signature(right):
                projection_conflicts.append((left, right, overlap, item))
            elif _is_residual(left) != _is_residual(right):
                residual_overlaps.append((left, right, overlap, item))
            else:
                unsafe_mapper_conflicts.append(item)

    assert not unsafe_mapper_conflicts, (
        "Different non-residual treaty categories with different rates remain "
        f"reachable from the same refined UI category: {unsafe_mapper_conflicts}"
    )

    for left, right, overlap, item in residual_overlaps:
        residual = left if _is_residual(left) else right
        specific = right if residual is left else left
        assert specific.priority < residual.priority, (
            "Residual royalty rule must have lower precedence in the direct "
            f"engine: {item}; priorities={specific.priority}/{residual.priority}"
        )

        package = load_legal_rules(RULE_DIR / f"{specific.recipient_country.lower()}.json")
        for ui_category in overlap:
            facts, legal_facts = _facts_satisfying(specific, ui_category)

            direct = evaluate_legal_rules(
                package,
                facts,
                as_of=date(2026, 8, 24),
                legal_facts=legal_facts,
            )
            assert direct.status == DecisionStatus.FINAL, (item, direct.explanation)
            assert direct.selected_rule_id == specific.rule_id, (item, direct.selected_rule_id)

            layered = evaluate_layered_rules(
                package,
                facts,
                as_of=date(2026, 8, 24),
                legal_facts=legal_facts,
            )
            assert layered.status == DecisionStatus.FINAL, (item, layered.explanation)
            assert layered.selected_rule_id == specific.rule_id, (item, layered.selected_rule_id)
            assert layered.candidate_rule_id == specific.rule_id, (item, layered.candidate_rule_id)

    for left, right, overlap, item in projection_conflicts:
        package = load_legal_rules(RULE_DIR / f"{left.recipient_country.lower()}.json")
        for ui_category in overlap:
            facts, legal_facts = _facts_satisfying(left, ui_category)

            direct = evaluate_legal_rules(
                package,
                facts,
                as_of=date(2026, 8, 24),
                legal_facts=legal_facts,
            )
            assert direct.status == DecisionStatus.REVIEW_REQUIRED, item
            assert direct.requires_review is True, item
            assert any(
                "Conflicting verified legal-rule projections" in line
                for line in direct.explanation
            ), (item, direct.explanation)

            layered = evaluate_layered_rules(
                package,
                facts,
                as_of=date(2026, 8, 24),
                legal_facts=legal_facts,
            )
            assert layered.status == DecisionStatus.REVIEW_REQUIRED, item
            assert layered.requires_review is True, item
            assert layered.rate is None, item
            assert layered.candidate_rate is None, item
            assert any(
                "Conflicting verified legal-rule projections" in line
                for line in layered.explanation
            ), (item, layered.explanation)
