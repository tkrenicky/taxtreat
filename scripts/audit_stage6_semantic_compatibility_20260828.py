from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from taxtreat.engine.legal_rule_engine import _royalty_categories_match


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"
DEFAULT_OUTPUT = ROOT / "reports" / "stage6_semantic_compatibility_inventory_20260828.json"

CONTROL_FACTS = {
    "fallback_case",
    "source_state_taxation",
    "general_article_11_2_rate",
}

BROWSER_DIRECT_FACTS = {
    "beneficial_owner",
    "recipient_is_treaty_resident",
    "permanent_establishment_connection",
    "recipient_entity_type",
    "ownership_percent",
    "direct_ownership",
    "direct_or_indirect_voting_ownership",
    "voting_ownership",
    "voting_power_control",
    "holding_period_months",
    "holding_period_years",
    "continuous_holding_period_days",
    "arm_length_amount",
    "royalty_category",
    "claim_not_effectively_connected_to_czech_pe",
    "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base",
}

# Values emitted by the profile form are intentionally coarse. They are not
# legal classifications and must never silently disprove a narrower treaty
# branch.
COARSE_BROWSER_FACTS = {
    "recipient_entity_type",
}

ATOMIC_ROYALTY_VALUES = {
    "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    "cinematographic_films_or_broadcast_media",
    "computer_software",
    "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "financial_lease_of_equipment",
    "operating_lease_or_other_use_of_equipment",
    "other",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _outcome(rule: dict[str, Any]) -> tuple[Any, ...]:
    return (
        rule.get("effect"),
        rule.get("rate"),
        rule.get("tax_treatment"),
    )


def build_inventory() -> dict[str, Any]:
    scopes: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_facts: dict[str, set[str]] = defaultdict(set)

    for path in sorted(RULE_DIR.glob("*.json")):
        payload = _load(path)
        country = path.stem.upper()
        for rule in payload.get("rules", []):
            if rule.get("effect") != "rate":
                continue
            income_type = str(rule.get("income_type") or "")
            if income_type not in {"dividend", "interest", "royalty"}:
                continue
            scopes[(country, income_type)].append(rule)
            for condition in rule.get("conditions", []):
                fact = str(condition.get("fact") or "")
                if fact:
                    all_facts[fact].add(country)

    rows: list[dict[str, Any]] = []
    multi_rate_rows: list[dict[str, Any]] = []

    for (country, income_type), rules in sorted(scopes.items()):
        treaty_like = [
            rule
            for rule in rules
            if rule.get("legal_layer") in {"treaty", "protocol", "mli"}
        ]
        outcomes = sorted(
            {
                str(_outcome(rule))
                for rule in treaty_like
            }
        )
        facts = sorted(
            {
                str(condition.get("fact"))
                for rule in treaty_like
                for condition in rule.get("conditions", [])
                if condition.get("fact") not in CONTROL_FACTS
            }
        )
        coarse = sorted(set(facts) & COARSE_BROWSER_FACTS)
        browser_direct = sorted(set(facts) & BROWSER_DIRECT_FACTS)
        non_browser = sorted(set(facts) - BROWSER_DIRECT_FACTS - CONTROL_FACTS)

        row = {
            "country": country,
            "income_type": income_type,
            "treaty_rule_count": len(treaty_like),
            "distinct_treaty_outcomes": outcomes,
            "multi_outcome": len(outcomes) > 1,
            "decision_facts": facts,
            "browser_direct_facts": browser_direct,
            "coarse_browser_facts": coarse,
            "non_browser_facts": non_browser,
        }
        rows.append(row)
        if row["multi_outcome"]:
            multi_rate_rows.append(row)

    royalty_multi = [
        row for row in multi_rate_rows if row["income_type"] == "royalty"
    ]

    royalty_atomic_coverage_gaps = []
    royalty_ambiguous_catchalls = []
    royalty_rules_by_country = defaultdict(list)

    for path in sorted(RULE_DIR.glob("*.json")):
        payload = _load(path)
        country = path.stem.upper()
        for rule in payload.get("rules", []):
            if (
                rule.get("income_type") == "royalty"
                and rule.get("legal_layer") in {"treaty", "protocol", "mli"}
            ):
                royalty_rules_by_country[country].append(rule)
                for condition in rule.get("conditions", []):
                    if (
                        condition.get("fact") == "royalty_category"
                        and condition.get("operator") == "=="
                        and condition.get("value")
                        in {"other", "all_other_article_12_royalties"}
                    ):
                        royalty_ambiguous_catchalls.append(
                            {
                                "country": country,
                                "rule_id": rule.get("rule_id"),
                                "rate": rule.get("rate"),
                                "value": condition.get("value"),
                            }
                        )

    for country, country_rules in sorted(royalty_rules_by_country.items()):
        category_rules = [
            rule
            for rule in country_rules
            if any(
                condition.get("fact") == "royalty_category"
                and condition.get("operator") == "=="
                for condition in rule.get("conditions", [])
            )
        ]
        if not category_rules:
            continue

        for atomic in sorted(ATOMIC_ROYALTY_VALUES):
            matched_rule_ids = [
                rule.get("rule_id")
                for rule in category_rules
                if any(
                    _royalty_categories_match(
                        atomic,
                        condition.get("value"),
                    )
                    for condition in rule.get("conditions", [])
                    if (
                        condition.get("fact") == "royalty_category"
                        and condition.get("operator") == "=="
                    )
                )
            ]
            if not matched_rule_ids:
                royalty_atomic_coverage_gaps.append(
                    {
                        "country": country,
                        "atomic_category": atomic,
                    }
                )

    entity_sensitive = [
        row
        for row in multi_rate_rows
        if "recipient_entity_type" in row["decision_facts"]
    ]

    return {
        "schema_version": 1,
        "purpose": (
            "Inventory of Stage 6 treaty decision complexity. This is a "
            "semantic compatibility audit, not a new legal approval."
        ),
        "counts": {
            "country_packages": len(list(RULE_DIR.glob("*.json"))),
            "scopes": len(rows),
            "multi_outcome_scopes": len(multi_rate_rows),
            "multi_outcome_royalty_scopes": len(royalty_multi),
            "entity_type_sensitive_multi_outcome_scopes": len(entity_sensitive),
            "unique_condition_facts": len(all_facts),
            "royalty_atomic_coverage_gaps": len(royalty_atomic_coverage_gaps),
            "royalty_ambiguous_catchall_rules": len(royalty_ambiguous_catchalls),
        },
        "atomic_browser_royalty_values": sorted(ATOMIC_ROYALTY_VALUES),
        "royalty_atomic_coverage_gaps": royalty_atomic_coverage_gaps,
        "royalty_ambiguous_catchalls": royalty_ambiguous_catchalls,
        "condition_fact_country_counts": {
            fact: len(countries)
            for fact, countries in sorted(all_facts.items())
        },
        "multi_outcome_scopes": multi_rate_rows,
        "all_scopes": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    inventory = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
