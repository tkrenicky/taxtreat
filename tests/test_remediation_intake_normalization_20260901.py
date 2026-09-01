import json
from pathlib import Path

from taxtreat.engine.dividend_rule_normalization import normalize_raw_legal_rule

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data" / "legal_rules_stage6"

EXPECTED_FACTS = {
    "CH": {
        "rule_id": "CZ-CH-DIVIDEND-SEMANTIC-REMEDIATION-5",
        "facts": {
            "recipient_entity_type",
            "recipient_is_partnership",
            "direct_ownership",
            "ownership_percent",
            "beneficial_owner",
            "recipient_is_treaty_resident",
            "permanent_establishment_connection",
        },
    },
    "EE": {
        "rule_id": "CZ-EE-DIVIDEND-CURRENT-1",
        "facts": {
            "recipient_entity_type",
            "recipient_is_partnership",
            "direct_ownership",
            "ownership_percent",
            "beneficial_owner",
        },
    },
    "LV": {
        "rule_id": "CZ-LV-DIVIDEND-CURRENT-1",
        "facts": {
            "recipient_entity_type",
            "recipient_is_partnership",
            "direct_ownership",
            "ownership_percent",
            "beneficial_owner",
        },
    },
    "VE": {
        "rule_id": "CZ-VE-DIVIDEND-CURRENT-1",
        "facts": {
            "recipient_entity_type",
            "recipient_is_partnership",
            "direct_ownership",
            "ownership_percent",
            "beneficial_owner",
        },
    },
    "KW": {
        "rule_id": "CZ-KW-DIVIDEND-CURRENT-1",
        "facts": {
            "treaty_specific_recipient_qualification",
            "beneficial_owner",
        },
    },
    "QA": {
        "rule_id": "CZ-QA-DIVIDEND-CURRENT-1",
        "facts": {
            "treaty_specific_recipient_qualification",
            "beneficial_owner",
        },
    },
}


def test_problematic_remediation_branches_are_intake_representable():
    for country, expected in EXPECTED_FACTS.items():
        payload = json.loads(
            (RULE_DIR / f"{country.lower()}.json").read_text(encoding="utf-8")
        )
        raw = next(
            rule for rule in payload["rules"]
            if rule["rule_id"] == expected["rule_id"]
        )
        normalized = normalize_raw_legal_rule(raw)
        facts = {condition["fact"] for condition in normalized["conditions"]}
        assert facts == expected["facts"], country

        entity_type_conditions = [
            condition
            for condition in normalized["conditions"]
            if condition["fact"] == "recipient_entity_type"
        ]
        assert all(
            condition["value"] in {"company", "individual", "fund", "other"}
            for condition in entity_type_conditions
        )


def test_czech_swiss_dividend_protocol_periods_do_not_overlap():
    payload = json.loads((RULE_DIR / "ch.json").read_text(encoding="utf-8"))
    normalized = {
        rule["rule_id"]: normalize_raw_legal_rule(rule)
        for rule in payload["rules"]
    }

    assert normalized["CZ-CH-DIVIDEND-SEMANTIC-REMEDIATION-5"]["effective_to"] == (
        "2013-12-31"
    )
    for rule_id in (
        "CZ-CH-DIVIDEND-CURRENT-2",
        "CZ-CH-DIVIDEND-CURRENT-3",
        "CZ-CH-DIVIDEND-CURRENT-4",
    ):
        assert normalized[rule_id]["effective_from"] == "2014-01-01"
        assert normalized[rule_id]["legal_layer"] == "protocol"
        assert normalized[rule_id]["source_id"] == "CH-FEDLEX-PROTOCOL-2012"

    assert "direct_ownership" in {
        condition["fact"]
        for condition in normalized["CZ-CH-DIVIDEND-CURRENT-2"]["conditions"]
    }
