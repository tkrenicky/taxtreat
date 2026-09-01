import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE = ROOT / "data" / "legal_rules_stage6" / "ad.json"


def test_ad_semantic_remediation_is_projected_and_fail_closed():
    payload = json.loads(RULE.read_text(encoding="utf-8"))
    rules = {row["rule_id"]: row for row in payload["rules"]}

    reduced = rules["CZ-AD-DIVIDEND-CURRENT-1"]
    fallback = rules["CZ-AD-DIVIDEND-CURRENT-2"]

    assert reduced["verification_status"] == "needs_review"
    assert reduced["conditions"] == [
        {
            "fact": "recipient_entity_type",
            "fact_source": "transaction",
            "operator": "==",
            "value": "company_other_than_partnership",
        },
        {
            "fact": "direct_ownership",
            "fact_source": "transaction",
            "operator": "==",
            "value": "true",
        },
        {
            "fact": "ownership_percent",
            "fact_source": "transaction",
            "operator": ">=",
            "value": "10",
        },
        {
            "fact": "beneficial_owner",
            "fact_source": "transaction",
            "operator": "==",
            "value": "true",
        },
    ]

    assert fallback["verification_status"] == "needs_review"
    assert fallback["conditions"] == [
        {
            "fact": "fallback_case",
            "fact_source": "transaction",
            "operator": "==",
            "value": "all_other_cases",
        },
        {
            "fact": "beneficial_owner",
            "fact_source": "transaction",
            "operator": "==",
            "value": "true",
        },
    ]

    production = payload["stage6_production"]
    assert production["package_sha256"] == (
        "6a2fecb997238bfcd6eb6eeee0e03d6add49c15b4485740cec50868de61aef1a"
    )
    assert production["production_approval"] == "not_approved"
    assert production["rule_promotion"] == "not_promoted"
    assert production["source_release"] == "not_released"
