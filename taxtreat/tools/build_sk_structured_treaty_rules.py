from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/sk_outbound"
SEMANTIC = BASE / "treaty_semantic_candidates.json"
ARTICLES = BASE / "treaty_article_machine_extraction.json"
COVERAGE = BASE / "human_review_coverage.json"
OUTPUT = ROOT / "data/legal_rules_sk"
SUMMARY = BASE / "structured_treaty_rule_materialization_summary.json"

RISKY_INTEREST = (
    "osloboden",
    "výlučne",
    "len v druhom",
    "bez ohľadu na ustanovenia odseku 2",
    "bez ohľadu na ustanovenia odseku 1",
    "nepresiahne:",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_safe_simple(scope: dict, article: dict) -> bool:
    rates = scope.get("rate_candidates") or []
    if len(rates) != 1:
        return False
    if scope.get("exclusive_residence_taxation_candidate"):
        return False
    if int(scope.get("ownership_linked_rate_candidate_count") or 0) != 0:
        return False
    if scope.get("holding_period_candidates"):
        return False
    if not scope.get("source_sha256"):
        return False
    if scope.get("semantic_status") != "machine_candidate_not_legal_conclusion":
        return False

    text = str(article.get("article_text") or "").lower()
    income = scope["income_type"]
    if income == "interest" and any(token in text for token in RISKY_INTEREST):
        return False
    if income == "dividend" and ("osloboden" in text or "nepresiahne:" in text):
        return False
    return True


def conditions(scope: dict) -> list[dict]:
    result = [{
        "fact": "recipient_is_treaty_resident",
        "fact_source": "transaction",
        "operator": "==",
        "value": True,
    }]
    rate = scope["rate_candidates"][0]
    if scope.get("beneficial_owner_wording_present") or rate.get("beneficial_owner_context"):
        result.append({
            "fact": "beneficial_owner",
            "fact_source": "transaction",
            "operator": "==",
            "value": True,
        })
    if scope.get("pe_or_fixed_base_carveout_wording_present"):
        result.append({
            "fact": "permanent_establishment_connection",
            "fact_source": "transaction",
            "operator": "==",
            "value": False,
        })
    return result


def main() -> int:
    semantic = load(SEMANTIC)
    articles = load(ARTICLES)
    coverage = load(COVERAGE)

    assert coverage["coverage"]["legal_review_covered_scopes"] == 225
    assert coverage["coverage"]["uncovered_scopes"] == 0
    assert coverage["individual_review"]["substantive_machine_discrepancies"] == 0

    article_by = {
        (row["recipient_country"], row["income_type"]): row
        for row in articles["scopes"]
    }

    grouped: dict[str, list[dict]] = defaultdict(list)
    unresolved = []
    materialized = []

    for scope in semantic["scopes"]:
        key = (scope["recipient_country"], scope["income_type"])
        article = article_by[key]
        if not is_safe_simple(scope, article):
            unresolved.append({
                "recipient_country": scope["recipient_country"],
                "income_type": scope["income_type"],
                "rate_candidates": [
                    row.get("rate_percent") for row in scope.get("rate_candidates", [])
                ],
                "exclusive_residence_taxation_candidate": bool(
                    scope.get("exclusive_residence_taxation_candidate")
                ),
                "ownership_linked_rate_candidate_count": int(
                    scope.get("ownership_linked_rate_candidate_count") or 0
                ),
                "holding_period_candidates": scope.get("holding_period_candidates", []),
            })
            continue

        country = scope["recipient_country"]
        income = scope["income_type"]
        rate = float(scope["rate_candidates"][0]["rate_percent"])
        article_text = str(article["article_text"])
        source_hash = str(scope["source_sha256"])
        rule = {
            "rule_id": f"SK-{country}-{income.upper()}-TREATY-SIMPLE-1",
            "income_type": income,
            "source_country": "SK",
            "recipient_country": country,
            "legal_instrument": "treaty",
            "legal_layer": "treaty",
            "article": str(scope["actual_article"]),
            "paragraph": None,
            "rate": rate,
            "priority": 600,
            "conditions": conditions(scope),
            "effect": "rate",
            "verification_status": "verified",
            "source_text": article_text,
            "source_id": f"SK-SLOVLEX-{source_hash[:16].upper()}",
            "source_url": scope["source_url"],
            "source_excerpt_hash": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
            "verification_authority": "sk_legal_review_coverage_pattern_reconciliation",
            "reviewer_id": "sk_legal_review_coverage",
            "reviewed_at": "2026-08-21",
            "approved_by": "structured_materialization_policy",
            "approved_at": "2026-08-31",
            "approval_dataset_release": coverage["dataset_release"],
            "approval_created_at": "2026-08-31",
            "dataset_release": "sk-structured-treaty-rules-2026-08-31.1",
            "evidence_source_ids": [f"SK-SLOVLEX-{source_hash[:16].upper()}"],
        }
        grouped[country].append(rule)
        materialized.append(f"SK-{country}-{income}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT.glob("*.json"):
        path.unlink()

    for country, rules in sorted(grouped.items()):
        payload = {
            "country_pair": {
                "source_country": "SK",
                "recipient_country": country,
            },
            "rules": sorted(rules, key=lambda row: (row["income_type"], row["rule_id"])),
        }
        (OUTPUT / f"{country.lower()}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    summary = {
        "schema_version": 1,
        "dataset_release": "sk-structured-treaty-rules-2026-08-31.1",
        "source_country": "SK",
        "total_scopes": 225,
        "materialized_scopes": len(materialized),
        "unresolved_scopes": len(unresolved),
        "materialized_country_packages": len(grouped),
        "materialized_scope_keys": sorted(materialized),
        "unresolved": unresolved,
        "policy": {
            "only_unambiguous_single_rate_scopes_materialized": True,
            "special_interest_exemptions_not_inferred": True,
            "ownership_linked_dividend_branches_not_inferred": True,
            "multi_rate_royalties_not_inferred": True,
            "czech_rule_reuse_forbidden": True,
            "release_remains_closed_until_all_225_scopes_are_structured_and_regression_tested": True,
        },
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"SK structured rules stage 1: {len(materialized)}/225 scopes")
    print(f"country packages: {len(grouped)}")
    print(f"unresolved: {len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
