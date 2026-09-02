from __future__ import annotations

from datetime import date
from pathlib import Path

from taxtreat.engine.layered_decision import evaluate_layered_rules
from taxtreat.engine.legal_rule_loader import load_legal_rules

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
AS_OF = date(2026, 8, 11)
RULE_CONTROL_FACTS = {"fallback_case", "source_state_taxation", "general_article_11_2_rate"}


def satisfying_value(operator, value):
    if operator == "==":
        return value
    if operator == "!=":
        if isinstance(value, bool):
            return not value
        if isinstance(value, (int, float)):
            return value + 1
        return "__tt_other__"
    if operator in {">=", "<="}:
        return value
    if operator == ">":
        return value + 1 if isinstance(value, (int, float)) else value
    if operator == "<":
        return value - 1 if isinstance(value, (int, float)) else value
    if operator == "in":
        return value[0] if isinstance(value, (list, tuple, set)) else value
    if operator == "not in":
        return "__tt_other__"
    raise AssertionError(f"unsupported operator {operator!r}")


def _condition_target(condition, facts, legal, determinations):
    return (
        legal
        if condition.fact_source == "legal"
        else determinations
        if condition.fact_source == "determination"
        else facts
    )


def complete_treaty_facts(country, treaty_rules):
    """Populate every fact used by treaty-rate branches.

    This verifier intentionally isolates the treaty fallback path. EU/domestic
    exemption eligibility is covered by dedicated tests and is excluded from
    the evaluated rule set below, so incomplete exemption facts cannot mask a
    treaty fallback regression with a fail-closed REVIEW_REQUIRED result.
    """
    facts = {
        "income_type": "dividend",
        "source_country": "CZ",
        "recipient_country": country,
        "beneficial_owner": True,
        "recipient_is_treaty_resident": True,
        "permanent_establishment_connection": False,
        "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base": True,
        "claim_not_effectively_connected_to_czech_pe": True,
    }
    legal = {}
    determinations = {}

    for rule in treaty_rules:
        for condition in rule.conditions:
            if condition.fact in RULE_CONTROL_FACTS:
                continue
            target = _condition_target(condition, facts, legal, determinations)
            if condition.fact not in target:
                target[condition.fact] = satisfying_value(
                    condition.operator,
                    condition.value,
                )

    return facts, legal, determinations


def main() -> int:
    tested = 0
    failures = []
    for path in sorted(RULE_DIR.glob("*.json")):
        rules = load_legal_rules(path)
        dividend = [
            rule for rule in rules
            if rule.source_country == "CZ"
            and rule.income_type == "dividend"
            and (rule.effective_from is None or rule.effective_from <= AS_OF)
            and (rule.effective_to is None or rule.effective_to >= AS_OF)
        ]
        treaty = [
            rule for rule in dividend
            if rule.effect == "rate"
            and rule.legal_layer in {"treaty", "protocol", "mli"}
            and rule.verification_status == "verified"
        ]
        relief = [
            rule for rule in dividend
            if rule.effect == "rate"
            and rule.legal_layer == "eu_relief"
            and rule.verification_status == "verified"
        ]
        if not treaty or not relief:
            continue

        country = treaty[0].recipient_country
        facts, legal, determinations = complete_treaty_facts(country, treaty)
        treaty_path_rules = [
            rule for rule in dividend
            if rule.legal_layer != "eu_relief"
        ]

        result = evaluate_layered_rules(
            treaty_path_rules,
            facts,
            as_of=AS_OF,
            legal_facts=legal,
            determinations=determinations,
        )
        tested += 1

        selected_layer = next(
            (
                rule.legal_layer
                for rule in treaty_path_rules
                if rule.rule_id == result.selected_rule_id
            ),
            None,
        )
        if result.status.value != "FINAL":
            failures.append(
                f"{country}: expected FINAL treaty fallback with all treaty facts completed, "
                f"got {result.status.value}; missing={result.missing_facts}; "
                f"candidate={result.candidate_rule_id}"
            )
            continue
        if selected_layer not in {"treaty", "protocol", "mli"}:
            structural_domestic = any(
                str(getattr(rule.tax_treatment, "value", rule.tax_treatment) or "")
                == "domestic_rate_applies"
                for rule in treaty
            )
            if not (
                structural_domestic
                and selected_layer == "domestic"
                and result.rate is not None
            ):
                failures.append(
                    f"{country}: expected treaty/protocol/MLI selection or a "
                    "verified treaty domestic_rate_applies handoff, "
                    f"got {result.selected_rule_id} ({selected_layer})"
                )
                continue
        if result.rate is None and str(result.tax_treatment.value if result.tax_treatment else "") != "exclusive_foreign_taxation":
            failures.append(
                f"{country}: final treaty outcome has neither rate nor exclusive-foreign treatment"
            )

    if failures:
        raise AssertionError(
            "Global dividend treaty fallback regression failures:\n" + "\n".join(failures)
        )
    if tested < 5:
        raise AssertionError(f"Suspiciously low cross-country coverage: {tested}")
    print(f"Global dividend treaty fallback: PASS ({tested} partner packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
