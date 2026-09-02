from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import CanonicalAnalysisRequest, analyze_transaction

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data/legal_reviews/sk_outbound/structured_treaty_rule_materialization_summary.json"
RULE_DIR = ROOT / "data/legal_rules_sk"


def test_sk_stage1_materializes_only_safe_scopes():
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert payload["source_country"] == "SK"
    assert payload["total_scopes"] == 225
    assert payload["materialized_scopes"] == 225
    assert payload["decision_materialized_scopes"] == 225
    assert payload["fail_closed_placeholder_scopes"] == 0
    assert payload["structured_scope_coverage"] == 225
    assert payload["unresolved_scopes"] == 0
    assert payload["materialized_country_packages"] == 75
    assert payload["policy"]["machine_rate_list_alone_is_never_sufficient_for_complex_branch_materialization"] is True
    assert payload["policy"]["unresolved_scopes_use_rate_null_fail_closed_placeholders"] is True
    assert payload["policy"]["rule_level_finalization_remains_closed_for_unresolved_scopes"] is True
    assert payload["policy"]["czech_rule_reuse_forbidden"] is True



def test_sk_source_text_recovery_closes_all_225_scopes_without_inventing_rates():
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    materialized = set(payload["materialized_scope_keys"])

    assert payload["unresolved"] == []
    assert len(materialized) == 225
    assert "SK-GR-dividend" in materialized
    assert "SK-LY-dividend" in materialized

    gr = json.loads((RULE_DIR / "gr.json").read_text(encoding="utf-8"))
    gr_dividend = [
        rule for rule in gr["rules"]
        if rule["income_type"] == "dividend" and rule["legal_layer"] == "treaty"
    ]
    assert any(
        rule.get("rate") is None
        and rule.get("tax_treatment") == "domestic_rate_applies"
        for rule in gr_dividend
    )

    ly = json.loads((RULE_DIR / "ly.json").read_text(encoding="utf-8"))
    ly_dividend = [
        rule for rule in ly["rules"]
        if rule["income_type"] == "dividend" and rule["legal_layer"] == "treaty"
    ]
    ly_rule = next(
        rule for rule in ly_dividend
        if rule.get("tax_treatment") == "exclusive_foreign_taxation"
    )
    assert any(
        condition.get("fact") == "ly_article_10_exclusive_residence_interpretation"
        and condition.get("fact_source") == "determination"
        for condition in ly_rule["conditions"]
    )


def test_every_materialized_rule_is_sk_only_and_source_backed():
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 75

    rule_count = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pair = payload["country_pair"]
        assert pair["source_country"] == "SK"
        for rule in payload["rules"]:
            rule_count += 1
            assert rule["source_country"] == "SK"
            assert rule["recipient_country"] == pair["recipient_country"]
            assert rule["legal_layer"] in {"treaty", "mli"}
            if rule["legal_layer"] == "treaty":
                assert rule["verification_status"] == "needs_review"
            else:
                assert rule["verification_status"] == "verified"
            assert rule["source_url"].startswith("https://")
            assert len(rule["source_excerpt_hash"]) == 64
            if rule["legal_layer"] == "treaty":
                assert rule["verification_authority"] == (
                    "sk_legal_review_coverage_pattern_reconciliation"
                )
            else:
                assert rule["verification_authority"] == (
                    "sk_mli_bilateral_adjudication_and_reconfirmation"
                )
            assert not rule["rule_id"].startswith("CZ-")

    assert rule_count >= 225  # 225 scope-covering treaty rules plus MLI gates/branch expansions


def test_materialized_sk_scope_reaches_candidate_but_release_manifest_keeps_it_closed():
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="AL",
            income_type="royalty",
            transaction_date=date(2026, 8, 31),
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
            },
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.candidate_rate == 8.0
    assert result.candidate_rule_id == "SK-AL-ROYALTY-TREATY-SIMPLE-1"
    assert result.requires_review is True
    assert any(
        "Rules awaiting independent approval" in line
        for line in result.explanation
    )


def test_unmaterialized_complex_scope_remains_fail_closed():
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="AL",
            income_type="interest",
            transaction_date=date(2026, 8, 31),
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
            },
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.selected_rule_id is None
