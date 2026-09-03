from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
RULE_DIRS = {
    "CZ": ROOT / "data" / "legal_rules_stage6",
    "SK": ROOT / "data" / "legal_rules_sk",
}
EXPECTED = {
    "CZ": {"countries": 101, "scopes": 303, "currency": "CZK", "dataset_prefix": "stage6-"},
    "SK": {"countries": 75, "scopes": 225, "currency": "EUR", "dataset_prefix": "sk-"},
}
INCOME_TYPES = ("dividend", "interest", "royalty")
DEFAULT_OUTPUT = ROOT / "reports" / "cz_sk_combinatorial_web_qa.json"
MIN_EXPECTED_SCENARIOS = 3000


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for source_country, directory in RULE_DIRS.items():
        countries: set[str] = set()
        scopes: set[tuple[str, str]] = set()
        conditions: dict[tuple[str, str], set[tuple[str, str, str, str]]] = defaultdict(set)

        for path in sorted(directory.glob("*.json")):
            package = load_json(path)
            pair = package.get("country_pair") or {}
            source = str(pair.get("source_country") or "").upper()
            recipient = str(pair.get("recipient_country") or "").upper()
            if source != source_country or not recipient:
                continue
            countries.add(recipient)
            for rule in package.get("rules", []):
                income_type = str(rule.get("income_type") or "")
                if income_type not in INCOME_TYPES:
                    continue
                scope = (recipient, income_type)
                scopes.add(scope)
                for condition in rule.get("conditions", []):
                    if not isinstance(condition, dict):
                        continue
                    fact = str(condition.get("fact") or "")
                    operator = str(condition.get("operator") or "")
                    fact_source = str(condition.get("fact_source") or "transaction")
                    if not fact or not operator or "value" not in condition:
                        continue
                    conditions[scope].add(
                        (
                            fact_source,
                            fact,
                            operator,
                            json.dumps(condition["value"], sort_keys=True, ensure_ascii=False),
                        )
                    )

        result[source_country] = {
            "countries": sorted(countries),
            "scopes": sorted(scopes),
            "conditions": conditions,
        }
    return result


def baseline_facts(income_type: str) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "recipient_entity_type": "company",
        "recipient_is_treaty_resident": True,
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
        "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base": True,
        "claim_not_effectively_connected_to_czech_pe": True,
        "ownership_percent": 100,
        "voting_ownership": 100,
        "direct_ownership": True,
        "holding_period_months": 24,
        "holding_period_will_reach_months": 24,
        "statutory_clawback_acknowledged": True,
        "recipient_is_qualifying_company_form": True,
        "recipient_is_tax_resident_in_eligible_jurisdiction": True,
        "recipient_subject_to_qualifying_corporate_tax": True,
        "recipient_has_no_tax_exemption_or_zero_rate_option": True,
        "recipient_is_parent_company": True,
        "arm_length_amount": True,
        "related_party_status": "unrelated",
        "royalty_category": "computer_software",
    }
    if income_type != "dividend":
        for key in (
            "ownership_percent",
            "voting_ownership",
            "direct_ownership",
            "holding_period_months",
            "holding_period_will_reach_months",
            "statutory_clawback_acknowledged",
            "recipient_is_parent_company",
        ):
            facts.pop(key, None)
    return facts


def baseline_determinations() -> dict[str, Any]:
    return {
        "treaty_ppt_passed": True,
        "mli_article_10_third_jurisdiction_pe_test_passed": True,
        "mli_article_12_dependent_agent_pe_status_resolved": True,
        "mli_article_13_specific_activity_pe_status_resolved": True,
        "mli_article_15_closely_related_enterprise_status_resolved": True,
    }


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def condition_values(operator: str, value: Any) -> tuple[Any, Any] | None:
    if operator in {"==", "is"}:
        if isinstance(value, bool):
            return value, not value
        if numeric(value):
            return value, value + 1
        if isinstance(value, str):
            return value, "__taxtreat_other__"
        return value, None

    if operator in {"!=", "is_not"}:
        if isinstance(value, bool):
            return (not value), value
        if numeric(value):
            return value + 1, value
        if isinstance(value, str):
            return "__taxtreat_other__", value
        return None

    if numeric(value):
        epsilon = 0.01 if isinstance(value, float) else 1
        if operator == ">=":
            return value, value - epsilon
        if operator == ">":
            return value + epsilon, value
        if operator == "<=":
            return value, value + epsilon
        if operator == "<":
            return value - epsilon, value

    if operator in {"in", "not in", "not_in"} and isinstance(value, list) and value:
        first = value[0]
        outsider: Any = "__taxtreat_other__"
        if all(numeric(item) for item in value):
            outsider = max(value) + 1
        if operator == "in":
            return first, outsider
        return outsider, first

    return None


def apply_condition(
    facts: dict[str, Any],
    determinations: dict[str, Any],
    *,
    fact_source: str,
    fact: str,
    value: Any,
) -> None:
    target = determinations if fact_source == "determination" else facts
    target[fact] = value


def base_payload(source_country: str, recipient_country: str, income_type: str) -> dict[str, Any]:
    currency = EXPECTED[source_country]["currency"]
    return {
        "source_country": source_country,
        "recipient_country": recipient_country,
        "income_type": income_type,
        "transaction_date": "2026-09-02",
        "facts": baseline_facts(income_type),
        "determinations": baseline_determinations(),
        "transaction_amount": {
            "amount": "100000",
            "currency": currency,
            "payment_date": "2026-09-02",
            "accounting_date": "2026-09-02",
        },
    }


def scenario_payloads(
    source_country: str,
    recipient_country: str,
    income_type: str,
    scope_conditions: set[tuple[str, str, str, str]],
) -> tuple[list[tuple[str, dict[str, Any]]], list[dict[str, Any]]]:
    scenarios: list[tuple[str, dict[str, Any]]] = [
        ("baseline", base_payload(source_country, recipient_country, income_type))
    ]

    unsupported_conditions: list[dict[str, Any]] = []
    for fact_source, fact, operator, encoded_value in sorted(scope_conditions):
        expected = json.loads(encoded_value)
        pair = condition_values(operator, expected)
        if pair is None:
            unsupported_conditions.append(
                {
                    "fact_source": fact_source,
                    "fact": fact,
                    "operator": operator,
                    "value": expected,
                }
            )
            continue
        satisfying, failing = pair
        for label, candidate in (("match", satisfying), ("boundary_or_fail", failing)):
            if candidate is None:
                continue
            payload = base_payload(source_country, recipient_country, income_type)
            apply_condition(
                payload["facts"],
                payload["determinations"],
                fact_source=fact_source,
                fact=fact,
                value=candidate,
            )
            scenarios.append(
                (
                    f"{fact_source}:{fact}:{operator}:{label}",
                    payload,
                )
            )

    # Web-visible cross-fact cases that are important even when a particular
    # treaty package does not repeat the fact in every rule.
    common = [
        ("treaty_resident_false", {"recipient_is_treaty_resident": False}),
        ("beneficial_owner_false", {"beneficial_owner": False}),
        ("pe_connection_true", {"permanent_establishment_connection": True}),
    ]
    if income_type == "dividend":
        common.extend(
            [
                ("ownership_zero", {"ownership_percent": 0}),
                ("ownership_10", {"ownership_percent": 10}),
                ("ownership_25", {"ownership_percent": 25}),
                ("ownership_50", {"ownership_percent": 50}),
                ("direct_ownership_false", {"direct_ownership": False}),
                ("holding_0m", {"holding_period_months": 0}),
                ("holding_12m", {"holding_period_months": 12}),
                ("holding_24m", {"holding_period_months": 24}),
            ]
        )
    elif income_type == "interest":
        common.extend(
            [
                ("arm_length_false", {"arm_length_amount": False}),
                ("related_party", {"related_party_status": "related"}),
            ]
        )
    else:
        for category in (
            "copyright",
            "computer_software",
            "film_tv_radio",
            "industrial_equipment",
            "industrial_ip_knowhow",
            "financial_lease",
            "operating_lease",
            "other",
        ):
            common.append((f"royalty_category_{category}", {"royalty_category": category}))

    for label, overrides in common:
        payload = base_payload(source_country, recipient_country, income_type)
        payload["facts"].update(overrides)
        scenarios.append((label, payload))

    deduped: dict[str, tuple[str, dict[str, Any]]] = {}
    for label, payload in scenarios:
        fingerprint = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        deduped.setdefault(fingerprint, (label, payload))
    return list(deduped.values()), unsupported_conditions


def validate_analysis(
    source_country: str,
    analysis: dict[str, Any],
    issues: list[str],
) -> None:
    expected_prefix = EXPECTED[source_country]["dataset_prefix"]
    if not str(analysis.get("dataset_version") or "").startswith(expected_prefix):
        issues.append("dataset_mismatch")

    selected = str(analysis.get("selected_rule_id") or analysis.get("candidate_rule_id") or "")
    if selected and not selected.startswith(f"{source_country}-"):
        issues.append(f"cross_source_rule:{selected}")

    for key in ("withholding_tax_calculation", "withholding_compliance_schedule"):
        item = analysis.get(key) or {}
        if item and item.get("source_country") != source_country:
            issues.append(f"{key}_source_mismatch")


def run_qa(*, include_reports: bool = True) -> dict[str, Any]:
    inv = inventory()
    client = TestClient(app)
    issues: list[dict[str, Any]] = []
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    scenario_count = 0
    report_count = 0
    deterministic_rechecks = 0
    scenario_samples: list[dict[str, Any]] = []

    for source_country, expected in EXPECTED.items():
        actual = inv[source_country]
        if len(actual["countries"]) != expected["countries"]:
            issues.append(
                {
                    "kind": "inventory_country_count",
                    "source_country": source_country,
                    "expected": expected["countries"],
                    "actual": len(actual["countries"]),
                }
            )
        if len(actual["scopes"]) != expected["scopes"]:
            issues.append(
                {
                    "kind": "inventory_scope_count",
                    "source_country": source_country,
                    "expected": expected["scopes"],
                    "actual": len(actual["scopes"]),
                }
            )

        for recipient_country, income_type in actual["scopes"]:
            scope_conditions = actual["conditions"].get((recipient_country, income_type), set())
            scenarios, unsupported_conditions = scenario_payloads(
                source_country,
                recipient_country,
                income_type,
                scope_conditions,
            )
            if unsupported_conditions:
                issues.append(
                    {
                        "kind": "unsupported_rule_condition",
                        "source_country": source_country,
                        "recipient_country": recipient_country,
                        "income_type": income_type,
                        "conditions": unsupported_conditions,
                    }
                )
            source_counts[source_country]["scopes"] += 1
            source_counts[source_country]["scenarios"] += len(scenarios)

            for local_index, (scenario_label, payload) in enumerate(scenarios):
                scenario_count += 1
                scenario_issues: list[str] = []

                analysis_response = client.post("/analysis", json=payload)
                if analysis_response.status_code != 200:
                    scenario_issues.append(f"analysis_http:{analysis_response.status_code}")
                    analysis: dict[str, Any] = {}
                else:
                    analysis = analysis_response.json()
                    validate_analysis(source_country, analysis, scenario_issues)

                lang = "en" if scenario_count % 2 else "cs"
                intake_response = client.post(f"/analysis/intake?lang={lang}", json=payload)
                if intake_response.status_code != 200:
                    scenario_issues.append(f"intake_http:{intake_response.status_code}")
                else:
                    intake_analysis = (intake_response.json().get("analysis") or {})
                    if analysis:
                        for key in ("status", "rate", "candidate_rate", "selected_rule_id", "candidate_rule_id"):
                            if intake_analysis.get(key) != analysis.get(key):
                                scenario_issues.append(f"intake_analysis_divergence:{key}")
                    validate_analysis(source_country, intake_analysis, scenario_issues)

                if include_reports:
                    report_payload = deepcopy(payload)
                    report_payload["facts"]["__report_language"] = lang
                    report_response = client.post("/analysis/report", json=report_payload)
                    report_count += 1
                    if report_response.status_code != 200:
                        scenario_issues.append(f"report_http:{report_response.status_code}")
                    else:
                        body = report_response.json()
                        report = body.get("report") or {}
                        scope = report.get("scope") or {}
                        if scope.get("source_country") != source_country:
                            scenario_issues.append("report_source_mismatch")
                        if scope.get("recipient_country") != recipient_country:
                            scenario_issues.append("report_recipient_mismatch")
                        if scope.get("income_type") != income_type:
                            scenario_issues.append("report_income_type_mismatch")
                        html = str(body.get("html") or "")
                        if source_country == "SK":
                            for marker in ("586/1992", "§ 38da", "Česká srážková daň"):
                                if marker in html:
                                    scenario_issues.append(f"cz_report_leak:{marker}")
                        else:
                            for marker in ("595/2003", "OZN4311v26", "Slovak withholding tax"):
                                if marker in html:
                                    scenario_issues.append(f"sk_report_leak:{marker}")

                if local_index == 0 or scenario_count % 17 == 0:
                    second = client.post("/analysis", json=payload)
                    deterministic_rechecks += 1
                    if second.status_code != analysis_response.status_code:
                        scenario_issues.append("nondeterministic_http")
                    elif second.status_code == 200 and second.json() != analysis:
                        scenario_issues.append("nondeterministic_analysis")

                if scenario_issues:
                    issues.append(
                        {
                            "kind": "scenario_failure",
                            "source_country": source_country,
                            "recipient_country": recipient_country,
                            "income_type": income_type,
                            "scenario": scenario_label,
                            "issues": sorted(set(scenario_issues)),
                        }
                    )

                if len(scenario_samples) < 30:
                    scenario_samples.append(
                        {
                            "source_country": source_country,
                            "recipient_country": recipient_country,
                            "income_type": income_type,
                            "scenario": scenario_label,
                            "status": analysis.get("status"),
                            "selected_rule_id": analysis.get("selected_rule_id"),
                            "candidate_rule_id": analysis.get("candidate_rule_id"),
                        }
                    )

    if scenario_count < MIN_EXPECTED_SCENARIOS:
        issues.append(
            {
                "kind": "insufficient_combinatorial_coverage",
                "minimum": MIN_EXPECTED_SCENARIOS,
                "actual": scenario_count,
            }
        )

    return {
        "schema_version": 1,
        "purpose": (
            "Condition-derived CZ/SK combinatorial web-contract QA. Every released "
            "dividend/interest/royalty scope is exercised with baseline, web-visible "
            "fact variants, and satisfy/fail or boundary variants derived from the "
            "actual structured rule conditions. Each scenario traverses analysis and "
            "localized intake; reports are also generated unless explicitly skipped."
        ),
        "counts": {
            "countries": {source: len(inv[source]["countries"]) for source in EXPECTED},
            "scopes": {source: len(inv[source]["scopes"]) for source in EXPECTED},
            "scenarios": scenario_count,
            "reports": report_count,
            "deterministic_rechecks": deterministic_rechecks,
            "issues": len(issues),
        },
        "source_counts": {
            source: dict(sorted(counter.items()))
            for source, counter in sorted(source_counts.items())
        },
        "minimum_expected_scenarios": MIN_EXPECTED_SCENARIOS,
        "fail_closed_on_unsupported_conditions": True,
        "pass": not issues,
        "issues": issues,
        "samples": scenario_samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-reports", action="store_true")
    args = parser.parse_args()

    result = run_qa(include_reports=not args.skip_reports)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    print(json.dumps(result["source_counts"], ensure_ascii=False, sort_keys=True))
    if result["issues"]:
        print(json.dumps(result["issues"][:40], ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
