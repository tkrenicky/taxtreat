from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "data" / "legal_rules_sk"
DEFAULT_OUTPUT = ROOT / "reports" / "stage7_sk_75_country_e2e_qa.json"
INCOME_TYPES = ("dividend", "interest", "royalty")
EXPECTED_COUNTRIES = 75
EXPECTED_SCOPES = 225


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _scope_inventory() -> list[tuple[str, str]]:
    scopes: set[tuple[str, str]] = set()
    for path in sorted(RULES_DIR.glob("*.json")):
        package = _load_json(path)
        pair = package.get("country_pair") or {}
        if str(pair.get("source_country") or "").upper() != "SK":
            continue
        country = str(pair.get("recipient_country") or "").upper()
        for rule in package.get("rules", []):
            income_type = str(rule.get("income_type") or "")
            if country and income_type in INCOME_TYPES:
                scopes.add((country, income_type))
    return sorted(scopes)


def _runtime_facts(income_type: str) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "recipient_entity_type": "company",
        "recipient_is_treaty_resident": True,
        "beneficial_owner": True,
        "permanent_establishment_connection": False,
        "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base": True,
        "claim_not_effectively_connected_to_czech_pe": True,
    }
    if income_type == "dividend":
        facts.update(
            {
                "ownership_percent": 100,
                "direct_ownership": True,
                "holding_period_months": 24,
                "voting_ownership": 100,
            }
        )
    elif income_type == "interest":
        facts.update({"arm_length_amount": True, "related_party_status": "unrelated"})
    else:
        facts.update(
            {
                "related_party_status": "unrelated",
                "royalty_category": "computer_software",
            }
        )
    return facts


def _determinations() -> dict[str, bool]:
    return {
        "treaty_ppt_passed": True,
        "mli_article_10_third_jurisdiction_pe_test_passed": True,
        "mli_article_13_specific_activity_pe_status_resolved": True,
    }


def run_qa(*, include_report_endpoint: bool = True) -> dict[str, Any]:
    scopes = _scope_inventory()
    countries = sorted({country for country, _ in scopes})
    client = TestClient(app)
    issues: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if len(countries) != EXPECTED_COUNTRIES:
        issues.append(
            {"kind": "inventory_country_count", "expected": EXPECTED_COUNTRIES, "actual": len(countries)}
        )
    if len(scopes) != EXPECTED_SCOPES:
        issues.append(
            {"kind": "inventory_scope_count", "expected": EXPECTED_SCOPES, "actual": len(scopes)}
        )

    for country, income_type in scopes:
        payload = {
            "source_country": "SK",
            "recipient_country": country,
            "income_type": income_type,
            "transaction_date": "2026-09-02",
            "facts": _runtime_facts(income_type),
            "determinations": _determinations(),
            "transaction_amount": {
                "amount": "100000",
                "currency": "EUR",
                "payment_date": "2026-09-02",
                "accounting_date": "2026-09-02",
            },
        }
        scope_issues: list[str] = []

        analysis_response = client.post("/analysis", json=payload)
        if analysis_response.status_code != 200:
            scope_issues.append(f"analysis_http_error:{analysis_response.status_code}")
            analysis: dict[str, Any] = {}
        else:
            analysis = analysis_response.json()
            if not str(analysis.get("dataset_version") or "").startswith("sk-"):
                scope_issues.append("analysis_dataset_mismatch")
            selected = str(analysis.get("selected_rule_id") or analysis.get("candidate_rule_id") or "")
            if selected and not selected.startswith("SK-"):
                scope_issues.append(f"non_sk_rule_selected:{selected}")
            calculation = analysis.get("withholding_tax_calculation") or {}
            schedule = analysis.get("withholding_compliance_schedule") or {}
            if calculation and calculation.get("source_country") != "SK":
                scope_issues.append("calculation_source_country_mismatch")
            if schedule and schedule.get("source_country") != "SK":
                scope_issues.append("schedule_source_country_mismatch")

        intake_response = client.post("/analysis/intake", json=payload)
        if intake_response.status_code != 200:
            scope_issues.append(f"intake_http_error:{intake_response.status_code}")
        else:
            intake = intake_response.json()
            intake_schedule = (intake.get("analysis") or {}).get(
                "withholding_compliance_schedule"
            ) or {}
            if intake_schedule.get("source_country") != "SK":
                scope_issues.append("intake_source_country_mismatch")

        if include_report_endpoint:
            report_response = client.post("/analysis/report", json=payload)
            if report_response.status_code != 200:
                scope_issues.append(f"report_http_error:{report_response.status_code}")
            else:
                report_payload = report_response.json()
                report = report_payload.get("report") or {}
                html = str(report_payload.get("html") or "")
                if (report.get("scope") or {}).get("source_country") != "SK":
                    scope_issues.append("report_source_country_mismatch")
                forbidden = ("586/1992", "§ 38da", "Česká srážková daň")
                leaks = [marker for marker in forbidden if marker in html]
                if leaks:
                    scope_issues.append(f"czech_report_leakage:{','.join(leaks)}")

        if scope_issues:
            issues.append(
                {
                    "kind": "scope_failure",
                    "country": country,
                    "income_type": income_type,
                    "issues": scope_issues,
                }
            )
        rows.append(
            {
                "country": country,
                "income_type": income_type,
                "status": analysis.get("status"),
                "selected_rule_id": analysis.get("selected_rule_id"),
                "candidate_rule_id": analysis.get("candidate_rule_id"),
                "scope_ok": not scope_issues,
            }
        )

    status_counts = Counter(str(row.get("status")) for row in rows)
    return {
        "schema_version": 1,
        "transaction_date": "2026-09-02",
        "purpose": (
            "SK source-country end-to-end QA: all 75 treaty partners and 225 "
            "dividend/interest/royalty scopes through analysis, intake and report."
        ),
        "counts": {
            "countries": len(countries),
            "scopes": len(scopes),
            "analysis_responses": len(rows),
            "scope_failures": sum(not row["scope_ok"] for row in rows),
            "issues": len(issues),
        },
        "status_counts": dict(sorted(status_counts.items())),
        "pass": not issues,
        "issues": issues,
        "scopes": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-report-endpoint", action="store_true")
    args = parser.parse_args()
    result = run_qa(include_report_endpoint=not args.skip_report_endpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    if result["issues"]:
        print(json.dumps(result["issues"][:20], ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
