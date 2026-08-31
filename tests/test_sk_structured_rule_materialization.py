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
    assert payload["materialized_scopes"] == 90
    assert payload["unresolved_scopes"] == 135
    assert payload["materialized_country_packages"] == 64
    assert payload["policy"]["only_unambiguous_single_rate_scopes_materialized"] is True
    assert payload["policy"]["special_interest_exemptions_not_inferred"] is True
    assert payload["policy"]["multi_rate_royalties_not_inferred"] is True
    assert payload["policy"]["czech_rule_reuse_forbidden"] is True


def test_every_materialized_rule_is_sk_only_and_source_backed():
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 64

    rule_count = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pair = payload["country_pair"]
        assert pair["source_country"] == "SK"
        for rule in payload["rules"]:
            rule_count += 1
            assert rule["source_country"] == "SK"
            assert rule["recipient_country"] == pair["recipient_country"]
            assert rule["legal_layer"] == "treaty"
            assert rule["verification_status"] == "needs_review"
            assert rule["source_url"].startswith("https://")
            assert len(rule["source_excerpt_hash"]) == 64
            assert rule["verification_authority"] == (
                "sk_legal_review_coverage_pattern_reconciliation"
            )
            assert not rule["rule_id"].startswith("CZ-")

    assert rule_count == 90


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
    assert "source_country_release_manifest" in result.missing_legal_layers
    assert any(
        "structured_sk_treaty_rules_not_materialized" in line
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
