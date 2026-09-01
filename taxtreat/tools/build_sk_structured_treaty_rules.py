from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/legal_reviews/sk_outbound"
SEMANTIC = BASE / "treaty_semantic_candidates.json"
ARTICLES = BASE / "treaty_article_machine_extraction.json"
COVERAGE = BASE / "human_review_coverage.json"
INVENTORY = BASE / "treaty_instrument_inventory.json"
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
    if scope.get("exclusive_residence_taxation_candidate"):
        return (
            scope.get("income_type") == "interest"
            and len(rates) <= 1
            and int(scope.get("ownership_linked_rate_candidate_count") or 0) == 0
            and not scope.get("holding_period_candidates")
            and bool(scope.get("source_sha256"))
            and scope.get("semantic_status") == "machine_candidate_not_legal_conclusion"
        )
    if len(rates) != 1:
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
    if income == "royalty":
        # A single machine-detected percentage is not sufficient when
        # Article 12(2) itself points to lettered royalty categories. Older
        # Slovak treaties often tax only one category at the detected rate
        # while another category is residence-state-only or uses another
        # ceiling. Keep those scopes out of the simple-rule layer.
        start = re.search(r"(?:\(2\)|\b2\.\s)", text)
        paragraph_2 = text[:1200]
        if start:
            tail = text[start.start():]
            end = re.search(r"(?:\(3\)|\b3\.\s)", tail[3:])
            paragraph_2 = tail[: (3 + end.start()) if end else 1200]
        if (
            "písm" in paragraph_2
            or "podľa písmena" in paragraph_2
            or "len v tomto" in paragraph_2
            or "iba v tomto" in paragraph_2
        ):
            return False
    return True


def conditions(scope: dict) -> list[dict]:
    result = [{
        "fact": "recipient_is_treaty_resident",
        "fact_source": "transaction",
        "operator": "==",
        "value": True,
    }]
    rate = (scope.get("rate_candidates") or [{}])[0]
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


def _article_paragraph_two(text: str) -> str:
    lowered = text.lower()
    start = re.search(r"(?:\(2\)|\b2\.\s)", lowered)
    if not start:
        return lowered[:2200]
    tail = lowered[start.start():]
    end = re.search(r"(?:\(3\)|\b3\.\s)", tail[3:])
    return tail[: (3 + end.start()) if end else 2600]


def _percent(value: str) -> float:
    return float(value.replace(",", "."))


def dividend_branches(scope: dict, article: dict) -> list[dict] | None:
    """Extract only source-text-explicit ordinary Article 10 branch pairs.

    The machine rate list is not trusted on its own. A branch is materialized
    only when paragraph 2 itself ties one percentage to an explicit ownership
    threshold and another percentage to all other cases. This covers the
    common OECD-style two-branch structure while leaving funds, public bodies,
    three-rate structures and unclear wording fail-closed.
    """
    if scope.get("income_type") != "dividend":
        return None
    text = _article_paragraph_two(str(article.get("article_text") or ""))
    if not text or not scope.get("source_sha256"):
        return None

    # Require an explicit fallback phrase; without it we cannot safely infer
    # complement logic from the set of percentages alone.
    fallback_match = re.search(
        r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,180}(?:vo\s+všetkých\s+ostatných\s+prípadoch|"
        r"v\s+ostatných\s+prípadoch|vo\s+všetkých\s+iných\s+prípadoch)",
        text,
        flags=re.S,
    )
    if not fallback_match:
        return None
    fallback_rate = _percent(fallback_match.group(1))

    ownership_match = re.search(
        r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,650}?"
        r"(?:priamo\s+(?:vlastní|má|drží)|hlasovac(?:ích|ie|ích\s+práv|ích\s+podielov)|"
        r"vlastní\s+priamo)[^.;]{0,260}?najmenej\s+([0-9]+(?:[,.][0-9]+)?)\s*%",
        text,
        flags=re.S,
    )
    if not ownership_match:
        # Some treaties put the threshold before the direct/voting qualifier.
        ownership_match = re.search(
            r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,650}?najmenej\s+"
            r"([0-9]+(?:[,.][0-9]+)?)\s*%[^.;]{0,260}?"
            r"(?:priamo|hlasovac)",
            text,
            flags=re.S,
        )
    if not ownership_match:
        return None

    qualifying_rate = _percent(ownership_match.group(1))
    threshold = _percent(ownership_match.group(2))
    if qualifying_rate == fallback_rate:
        return None

    # Cross-check both rates against the semantic candidate list, but do not
    # require the noisy list to be unique or perfectly deduplicated.
    candidate_rates = {
        float(row["rate_percent"])
        for row in scope.get("rate_candidates", [])
        if row.get("rate_percent") is not None
    }
    if qualifying_rate not in candidate_rates or fallback_rate not in candidate_rates:
        return None

    qualifying_context = ownership_match.group(0)
    qualifying_conditions = conditions(scope)
    qualifying_conditions.append({
        "fact": "recipient_entity_type",
        "fact_source": "transaction",
        "operator": "in",
        "value": ["company", "corporate", "company_other_than_partnership"],
    })
    if "hlasovac" in qualifying_context:
        qualifying_conditions.append({
            "fact": "voting_interest_percent",
            "fact_source": "transaction",
            "operator": ">=",
            "value": threshold,
        })
    else:
        qualifying_conditions.extend([
            {
                "fact": "direct_ownership",
                "fact_source": "transaction",
                "operator": "==",
                "value": True,
            },
            {
                "fact": "ownership_percent",
                "fact_source": "transaction",
                "operator": ">=",
                "value": threshold,
            },
        ])

    holding = re.search(
        r"(?:počas\s+obdobia\s+)?(365)\s+dní",
        qualifying_context,
    )
    if holding:
        qualifying_conditions.append({
            "fact": "holding_period_days",
            "fact_source": "transaction",
            "operator": ">=",
            "value": int(holding.group(1)),
        })

    return [
        {
            "rate": qualifying_rate,
            "priority": 650,
            "conditions": qualifying_conditions,
            "branch_kind": "ownership_qualified",
        },
        {
            "rate": fallback_rate,
            "priority": 600,
            "conditions": conditions(scope),
            "branch_kind": "ordinary_fallback",
        },
    ]


def _make_rule(
    *,
    scope: dict,
    article: dict,
    country: str,
    income: str,
    rate: float,
    priority: int,
    rule_conditions: list[dict],
    rule_suffix: str,
    treaty_valid_from: dict[str, str],
    coverage: dict,
    tax_treatment: str | None = None,
) -> dict:
    article_text = str(article["article_text"])
    source_hash = str(scope["source_sha256"])
    rule = {
        "rule_id": f"SK-{country}-{income.upper()}-TREATY-{rule_suffix}",
        "income_type": income,
        "source_country": "SK",
        "recipient_country": country,
        "legal_instrument": "treaty",
        "legal_layer": "treaty",
        "article": str(scope["actual_article"]),
        "paragraph": None,
        "rate": rate,
        "priority": priority,
        "conditions": rule_conditions,
        "effect": "rate",
        "effective_from": treaty_valid_from[country],
        "verification_status": "needs_review",
        "source_text": article_text,
        "source_id": f"SK-SLOVLEX-{source_hash[:16].upper()}",
        "source_url": scope["source_url"],
        "source_excerpt_hash": hashlib.sha256(article_text.encode("utf-8")).hexdigest(),
        "verification_authority": "sk_legal_review_coverage_pattern_reconciliation",
        "reviewer_id": "sk_legal_review_coverage",
        "reviewed_at": "2026-08-21",
        "approval_dataset_release": coverage["dataset_release"],
        "approval_created_at": "2026-09-01",
        "dataset_release": "sk-structured-treaty-rules-2026-09-01.2",
        "evidence_source_ids": [f"SK-SLOVLEX-{source_hash[:16].upper()}"],
        "decision_status": "REVIEW_REQUIRED",
        "final_rate_allowed": False,
        "automatic_production_approval_forbidden": True,
    }
    if tax_treatment:
        rule["tax_treatment"] = tax_treatment
    return rule


def main() -> int:
    semantic = load(SEMANTIC)
    articles = load(ARTICLES)
    coverage = load(COVERAGE)
    inventory = load(INVENTORY)
    treaty_valid_from = {
        row["recipient_country"]: row["treaty_valid_from"]
        for row in inventory["relationships"]
    }

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
    materialization_modes = defaultdict(int)

    for scope in semantic["scopes"]:
        key = (scope["recipient_country"], scope["income_type"])
        article = article_by[key]
        country = scope["recipient_country"]
        income = scope["income_type"]

        branches = dividend_branches(scope, article)
        if branches:
            for index, branch in enumerate(branches, start=1):
                grouped[country].append(_make_rule(
                    scope=scope,
                    article=article,
                    country=country,
                    income=income,
                    rate=float(branch["rate"]),
                    priority=int(branch["priority"]),
                    rule_conditions=branch["conditions"],
                    rule_suffix=f"DIVIDEND-BRANCH-{index}",
                    treaty_valid_from=treaty_valid_from,
                    coverage=coverage,
                ))
            materialized.append(f"SK-{country}-{income}")
            materialization_modes["source_text_dividend_branch_pair"] += 1
            continue

        if not is_safe_simple(scope, article):
            unresolved.append({
                "recipient_country": country,
                "income_type": income,
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

        exclusive_residence = bool(scope.get("exclusive_residence_taxation_candidate"))
        rate = (
            0.0
            if exclusive_residence
            else float(scope["rate_candidates"][0]["rate_percent"])
        )
        grouped[country].append(_make_rule(
            scope=scope,
            article=article,
            country=country,
            income=income,
            rate=rate,
            priority=600,
            rule_conditions=conditions(scope),
            rule_suffix="SIMPLE-1",
            treaty_valid_from=treaty_valid_from,
            coverage=coverage,
            tax_treatment="exclusive_foreign_taxation" if exclusive_residence else None,
        ))
        materialized.append(f"SK-{country}-{income}")
        materialization_modes[
            "exclusive_residence_interest" if exclusive_residence else "simple_single_rate"
        ] += 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT.glob("*.json"):
        path.unlink()

    for country, rules in sorted(grouped.items()):
        payload = {
            "country_pair": {
                "source_country": "SK",
                "recipient_country": country,
            },
            "rules": sorted(rules, key=lambda row: (row["income_type"], -row["priority"], row["rule_id"])),
        }
        (OUTPUT / f"{country.lower()}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    summary = {
        "schema_version": 2,
        "dataset_release": "sk-structured-treaty-rules-2026-09-01.2",
        "source_country": "SK",
        "total_scopes": 225,
        "materialized_scopes": len(materialized),
        "unresolved_scopes": len(unresolved),
        "materialized_country_packages": len(grouped),
        "materialized_scope_keys": sorted(materialized),
        "materialization_modes": dict(sorted(materialization_modes.items())),
        "unresolved": unresolved,
        "policy": {
            "machine_rate_list_alone_is_never_sufficient_for_complex_branch_materialization": True,
            "source_text_explicit_dividend_branch_pairs_materialized": True,
            "source_text_fallback_phrase_required_for_dividend_branch_pair": True,
            "stage_rules_remain_needs_review_until_all_protocol_mli_and_release_gates_are_satisfied": True,
            "special_interest_exemptions_not_inferred": True,
            "explicit_exclusive_residence_interest_scopes_materialized_as_structural_zero": True,
            "multi_rate_royalties_not_inferred": True,
            "czech_rule_reuse_forbidden": True,
            "release_remains_closed_until_all_225_scopes_are_structured_and_regression_tested": True,
            "automatic_production_approval_forbidden": True,
        },
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"SK structured rules: {len(materialized)}/225 scopes")
    print(f"country packages: {len(grouped)}")
    print(f"unresolved: {len(unresolved)}")
    print(f"modes: {dict(sorted(materialization_modes.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
