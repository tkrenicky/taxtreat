import json
from pathlib import Path

from taxtreat.engine.legal_rule_loader import (
    load_legal_rules,
)
from taxtreat.engine.legal_rule_engine import (
    evaluate_legal_rules,
)

RULE_DIR = Path("data/legal_rules")
AUDIT_PATH = Path(
    "data/legal_reviews/global_cz_outbound/"
    "final23_runtime_catalog_integration.json"
)

def paths():
    return sorted(
        RULE_DIR.glob("final23_*.json")
    )

def test_18_catalog_files_exist():
    assert len(paths()) == 18

def test_all_78_candidate_rules_load():
    total = 0

    for path in paths():
        rules = load_legal_rules(path)
        total += len(rules)

        for rule in rules:
            assert (
                rule.verification_status
                == "needs_review"
            )

            assert rule.source_id
            assert rule.source_text
            assert rule.source_excerpt_hash
            assert rule.evidence_source_ids
            assert rule.dataset_release

    assert total == 78

def test_candidate_rules_never_return_final():
    for path in paths():
        rules = load_legal_rules(path)

        grouped = {}

        for rule in rules:
            grouped.setdefault(
                rule.income_type,
                [],
            ).append(rule)

        for income, scoped in grouped.items():
            facts = {
                "source_country": "CZ",
                "recipient_country":
                    scoped[0].recipient_country,
                "income_type": income,
                "recipient_is_treaty_resident":
                    True,
                "beneficial_owner": True,
                "permanent_establishment_connection":
                    False,
                "recipient_entity_type":
                    "company",
                "ownership_percent": 100,
                "holding_period_months": 120,
                "holding_period_will_reach_months":
                    120,
                "statutory_clawback_acknowledged":
                    True,
                "related_party_status": True,
                "royalty_classification":
                    "industrial",
            }

            result = evaluate_legal_rules(
                scoped,
                facts,
            )

            assert result.status.value != "FINAL"
            assert result.requires_review is True

def test_complex_conditions_preserved_in_audit():
    audit = json.loads(
        AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert audit["rule_count"] == 78

    assert (
        audit["runtime_projection_complete_count"]
        + audit["runtime_projection_blocked_count"]
        == 78
    )

    for row in audit["rules"]:
        if row["complex_condition_count"]:
            assert row["complex_conditions"]
            assert (
                row["runtime_projection_complete"]
                is False
            )

        assert (
            row["verified_promotion_allowed"]
            is False
        )

def test_no_candidate_is_marked_active_or_verified():
    audit = json.loads(
        AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert audit["verified_rule_count"] == 0
    assert audit["active_rule_count"] == 0
