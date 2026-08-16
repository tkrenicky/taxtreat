from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from taxtreat.services.legal_sources import build_legal_path


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "data" / "legal_rules_stage6"
CANONICAL = ROOT / "data" / "legal_texts" / "canonical_provisions.json"
DEFAULT_OUTPUT = ROOT / "reports" / "stage7_101_country_e2e_qa.json"
INCOME_TYPES = ("dividend", "interest", "royalty")
EXPECTED_COUNTRIES = 101
EXPECTED_SCOPES = 303
EXPECTED_CANONICAL = 302
TEXT_SOURCE_STATUS = "official_esbirka_structured_text_pdf_anchored"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _scope_inventory() -> list[tuple[str, str]]:
    scopes: set[tuple[str, str]] = set()
    for path in sorted(RULES_DIR.glob("*.json")):
        package = _load_json(path)
        pair = package.get("country_pair") or {}
        country = str(pair.get("recipient_country") or "").upper()
        if not country:
            continue
        for rule in package.get("rules", []):
            income_type = str(rule.get("income_type") or "")
            if income_type in INCOME_TYPES:
                scopes.add((country, income_type))
    return sorted(scopes)


def _canonical_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _complete_runtime_facts(income_type: str) -> dict[str, Any]:
    """Supply affirmative transaction-gate facts without asserting a treaty branch.

    The 303-scope portion is an endpoint/integration smoke test. Treaty branch
    selection remains governed by the actual country rules and may still be
    conditional or require additional rule-specific facts.
    """

    facts: dict[str, Any] = {
        "recipient_tax_residence": "confirmed",
        "recipient_legal_form": "company",
        "beneficial_owner": True,
        "beneficial_owner_confirmed": True,
        "anti_abuse_review_passed": True,
        "residence_certificate_available": True,
        "no_pe_connection": True,
        "pe_connection": False,
    }
    if income_type == "dividend":
        facts.update({
            "ownership_percent": 100,
            "direct_ownership": True,
            "holding_period_months": 24,
            "recipient_is_qualifying_company": True,
        })
    elif income_type == "interest":
        facts["related_party_status"] = "unrelated"
    elif income_type == "royalty":
        facts.update({
            "related_party_status": "unrelated",
            "royalty_category": (
                "software_patent_trademark_design_model_plan_secret_formula_process_knowhow"
            ),
        })
    return facts


def _verify_canonical_legal_paths(
    canonical: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Exercise the production legal-path service for every canonical treaty article."""

    issues: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for key, provision in sorted(canonical.items()):
        pair, layer, article = key.split("|", 2)
        source_country, recipient_country = pair.split("-", 1)
        item_issues: list[str] = []

        citation = {
            "rule_id": f"QA-{recipient_country}-{article}",
            "legal_layer": layer,
            "legal_instrument": "treaty",
            "article": article,
            "source_url": provision.get("source_url"),
        }
        path = build_legal_path(
            [citation],
            source_country=source_country,
            recipient_country=recipient_country,
            selected_rule_id=citation["rule_id"],
        )
        treaty_items = [
            item for item in path
            if item.get("legal_layer") == "treaty"
            and str(item.get("article") or "") == article
        ]
        if len(treaty_items) != 1:
            item_issues.append(f"treaty_path_count:{len(treaty_items)}")
        else:
            item = treaty_items[0]
            text = str(item.get("official_text") or "")
            if text != provision.get("text"):
                item_issues.append("official_text_mismatch")
            if item.get("official_text_sha256") != provision.get("verified_text_sha256"):
                item_issues.append("text_hash_mismatch")
            if item.get("official_pdf_sha256") != provision.get("official_pdf_sha256"):
                item_issues.append("pdf_hash_mismatch")
            if item.get("text_source_status") != TEXT_SOURCE_STATUS:
                item_issues.append("unexpected_text_source_status")
            if not text or _canonical_hash(text) != provision.get("verified_text_sha256"):
                item_issues.append("runtime_text_digest_mismatch")
            if item.get("source_url") != provision.get("source_url"):
                item_issues.append("source_url_mismatch")

        if item_issues:
            issues.append({
                "kind": "canonical_legal_path_failure",
                "key": key,
                "issues": item_issues,
            })
        rows.append({
            "key": key,
            "country": recipient_country,
            "article": article,
            "ok": not item_issues,
        })
    return issues, rows


def run_qa(*, include_report_endpoint: bool = True) -> dict[str, Any]:
    canonical = _load_json(CANONICAL)
    scopes = _scope_inventory()
    countries = sorted({country for country, _ in scopes})
    client = TestClient(app)
    issues: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if len(countries) != EXPECTED_COUNTRIES:
        issues.append({
            "kind": "inventory_country_count",
            "expected": EXPECTED_COUNTRIES,
            "actual": len(countries),
        })
    if len(scopes) != EXPECTED_SCOPES:
        issues.append({
            "kind": "inventory_scope_count",
            "expected": EXPECTED_SCOPES,
            "actual": len(scopes),
        })
    if len(canonical) != EXPECTED_CANONICAL:
        issues.append({
            "kind": "canonical_corpus_count",
            "expected": EXPECTED_CANONICAL,
            "actual": len(canonical),
        })

    canonical_issues, canonical_rows = _verify_canonical_legal_paths(canonical)
    issues.extend(canonical_issues)

    for country, income_type in scopes:
        payload = {
            "source_country": "CZ",
            "recipient_country": country,
            "income_type": income_type,
            "transaction_date": "2026-08-16",
            "facts": _complete_runtime_facts(income_type),
            "determinations": {},
        }
        scope_issues: list[str] = []
        response = client.post("/analysis", json=payload)
        if response.status_code != 200:
            issues.append({
                "kind": "analysis_http_error",
                "country": country,
                "income_type": income_type,
                "status_code": response.status_code,
                "detail": response.text[:1000],
            })
            continue

        analysis = response.json()
        if "status" not in analysis or "legal_path" not in analysis:
            scope_issues.append("analysis_shape_invalid")

        # If the actual rule engine emits a treaty citation for this scenario,
        # it must already be canonical and PDF-anchored. We do not require a
        # treaty citation for every synthetic transaction because rule-specific
        # eligibility remains intentionally fail-closed.
        for item in analysis.get("legal_path", []):
            if item.get("legal_layer") != "treaty":
                continue
            article = str(item.get("article") or "")
            key = f"CZ-{country}|treaty|{article}"
            provision = canonical.get(key)
            if provision is None:
                scope_issues.append(f"canonical_key_missing:{key}")
                continue
            if item.get("official_text") != provision.get("text"):
                scope_issues.append(f"runtime_canonical_text_mismatch:{key}")
            if item.get("official_pdf_sha256") != provision.get("official_pdf_sha256"):
                scope_issues.append(f"runtime_pdf_hash_mismatch:{key}")

        intake_response = client.post("/analysis/intake", json=payload)
        if intake_response.status_code != 200:
            scope_issues.append(f"intake_http_error:{intake_response.status_code}")
        else:
            intake_payload = intake_response.json()
            if "analysis" not in intake_payload or "intake" not in intake_payload:
                scope_issues.append("intake_shape_invalid")

        if include_report_endpoint:
            report_response = client.post("/analysis/report", json=payload)
            if report_response.status_code != 200:
                scope_issues.append(f"report_http_error:{report_response.status_code}")
            else:
                report_payload = report_response.json()
                if not report_payload.get("report") or not report_payload.get("html"):
                    scope_issues.append("report_shape_invalid")

        if scope_issues:
            issues.append({
                "kind": "scope_failure",
                "country": country,
                "income_type": income_type,
                "issues": scope_issues,
            })

        treaty_path = [
            item for item in analysis.get("legal_path", [])
            if item.get("legal_layer") == "treaty"
        ]
        rows.append({
            "country": country,
            "income_type": income_type,
            "status": analysis.get("status"),
            "rate": analysis.get("rate"),
            "candidate_rate": analysis.get("candidate_rate"),
            "selected_rule_id": analysis.get("selected_rule_id"),
            "candidate_rule_id": analysis.get("candidate_rule_id"),
            "missing_facts": analysis.get("missing_facts"),
            "treaty_path_articles": [
                str(item.get("article") or "") for item in treaty_path
            ],
            "treaty_path_count": len(treaty_path),
            "scope_ok": not scope_issues,
        })

    status_counts = Counter(str(row.get("status")) for row in rows)
    result = {
        "schema_version": 2,
        "transaction_date": "2026-08-16",
        "purpose": (
            "Stage 7 integration QA: all 303 released CZ outbound scopes through "
            "analysis/intake/report plus all 302 canonical treaty provisions through "
            "the production legal-path service."
        ),
        "counts": {
            "countries": len(countries),
            "scopes": len(scopes),
            "canonical_provisions": len(canonical),
            "canonical_legal_paths_checked": len(canonical_rows),
            "canonical_legal_path_failures": sum(not row["ok"] for row in canonical_rows),
            "analysis_responses": len(rows),
            "scope_failures": sum(not row["scope_ok"] for row in rows),
            "issues": len(issues),
        },
        "status_counts": dict(sorted(status_counts.items())),
        "pass": not issues,
        "issues": issues,
        "canonical_legal_paths": canonical_rows,
        "scopes": rows,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-report-endpoint",
        action="store_true",
        help="Skip /analysis/report calls for a faster diagnostic run.",
    )
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
