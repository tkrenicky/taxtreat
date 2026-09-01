from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.services.report_locales import english_excerpt_for_citation


ROOT = Path(__file__).resolve().parents[1]
CZ_COVERAGE = ROOT / "reports" / "treaty_en_rule_summary_coverage_20260826.json"
SK_PARTNERS = ROOT / "data" / "sk_treaty_partners.json"
SK_RULES = ROOT / "data" / "legal_rules_sk"
SK_INCOMES = {"dividend", "interest", "royalty"}
LEGAL_LAYERS = {"treaty", "protocol", "mli"}


def verify_dual_source_en_locale_coverage() -> dict[str, Any]:
    cz = json.loads(CZ_COVERAGE.read_text(encoding="utf-8"))
    if (
        cz.get("partner_count") != 100
        or cz.get("pass_count") != 100
        or float(cz.get("coverage_percent") or 0) != 100.0
    ):
        raise AssertionError(
            "CZ English treaty locale coverage is not 100/100."
        )

    partners = json.loads(SK_PARTNERS.read_text(encoding="utf-8"))
    if len(partners) != 75:
        raise AssertionError(f"Expected 75 SK treaty partners, got {len(partners)}.")

    expected_scopes = {
        (str(partner["iso2"]).upper(), income)
        for partner in partners
        for income in SK_INCOMES
    }
    covered_scopes: set[tuple[str, str]] = set()
    rule_count = 0
    verified_count = 0
    review_required_count = 0

    for partner in partners:
        country = str(partner["iso2"]).upper()
        path = SK_RULES / f"{country.lower()}.json"
        if not path.is_file():
            raise AssertionError(f"Missing SK rule file for {country}.")
        payload = json.loads(path.read_text(encoding="utf-8"))

        pair = payload.get("country_pair") or {}
        if (
            str(pair.get("source_country") or "").upper() != "SK"
            or str(pair.get("recipient_country") or "").upper() != country
        ):
            raise AssertionError(f"Invalid SK rule pair identity for {country}.")

        for rule in payload.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            if str(rule.get("legal_layer") or "") not in LEGAL_LAYERS:
                continue
            if str(rule.get("verification_status") or "") not in {
                "verified",
                "needs_review",
            }:
                continue

            rule_id = str(rule.get("rule_id") or "")
            if not rule_id:
                raise AssertionError(f"Missing SK rule id for {country}.")

            summary = english_excerpt_for_citation(
                {
                    "rule_id": rule_id,
                    "article": rule.get("article"),
                    "legal_layer": rule.get("legal_layer"),
                },
                country,
                "SK",
            )
            if not summary:
                raise AssertionError(f"Missing SK English summary for {rule_id}.")
            if summary.get("excerpt_language") != "en":
                raise AssertionError(f"Non-English SK summary for {rule_id}.")
            if "not treaty wording" not in str(
                summary.get("excerpt_status_label") or ""
            ).lower():
                raise AssertionError(
                    f"SK summary provenance is not explicit for {rule_id}."
                )
            excerpt = str(summary.get("excerpt") or "")
            if "Czech source-state" in excerpt or "Czech treaty" in excerpt:
                raise AssertionError(f"CZ source-country leakage in {rule_id}.")
            if summary.get("excerpt_source_url") != rule.get("source_url"):
                raise AssertionError(f"SK source URL mismatch for {rule_id}.")

            status = str(summary.get("excerpt_status") or "")
            if status == "verified_structured_rule_summary":
                verified_count += 1
            elif status == "review_required_structured_rule_summary":
                review_required_count += 1
                if (
                    "review-required" not in excerpt.lower()
                    and "no final" not in excerpt.lower()
                ):
                    raise AssertionError(
                        f"Review-required SK summary is not fail-closed: {rule_id}."
                    )
            else:
                raise AssertionError(
                    f"Unexpected SK English summary status for {rule_id}: {status}."
                )

            income = str(rule.get("income_type") or "")
            if income in SK_INCOMES:
                covered_scopes.add((country, income))
            rule_count += 1

    if covered_scopes != expected_scopes:
        missing = sorted(expected_scopes - covered_scopes)
        raise AssertionError(f"Missing SK English income scopes: {missing}")

    # Explicit cross-source isolation checks: the same recipient must resolve
    # from the selected source-country corpus, never from the other country's.
    sk_at = english_excerpt_for_citation(
        {
            "rule_id": "SK-AT-INTEREST-TREATY-INTEREST-RESIDENCE-ONLY",
            "article": "11",
            "legal_layer": "treaty",
        },
        "AT",
        "SK",
    )
    if not sk_at or "Slovak source-country legal data" not in sk_at["excerpt"]:
        raise AssertionError("SK->AT did not resolve from the SK corpus.")

    cz_at = english_excerpt_for_citation(
        {
            "rule_id": "CZ-AT-ROYALTY-CURRENT-1",
            "article": "12",
            "legal_layer": "treaty",
        },
        "AT",
        "CZ",
    )
    if not cz_at or "Slovak source-country legal data" in cz_at["excerpt"]:
        raise AssertionError("CZ->AT locale resolution crossed into SK.")

    return {
        "cz_partner_count": 100,
        "cz_pass_count": 100,
        "cz_coverage_percent": 100.0,
        "sk_partner_count": len(partners),
        "sk_income_scope_count": len(covered_scopes),
        "sk_rule_summary_count": rule_count,
        "sk_verified_summary_count": verified_count,
        "sk_review_required_summary_count": review_required_count,
    }


def main() -> int:
    result = verify_dual_source_en_locale_coverage()
    print(
        "Dual-source EN locale coverage: "
        f"CZ {result['cz_pass_count']}/{result['cz_partner_count']} partners; "
        f"SK {result['sk_partner_count']}/{result['sk_partner_count']} partners, "
        f"{result['sk_income_scope_count']}/225 income scopes; "
        f"{result['sk_rule_summary_count']} SK treaty/protocol/MLI rules "
        f"({result['sk_verified_summary_count']} verified, "
        f"{result['sk_review_required_summary_count']} review-required)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
