from __future__ import annotations

import json
from pathlib import Path


RULE_DIR = Path("data/legal_rules_stage6")

REGISTRY_PATH = Path(
    "data/registries/legal_condition_fact_registry.json"
)


def _registry():
    return json.loads(
        REGISTRY_PATH.read_text()
    )


def _rules():
    files = sorted(
        RULE_DIR.glob("*.json")
    )

    assert len(files) == 101

    for path in files:
        payload = json.loads(
            path.read_text()
        )

        rules = payload.get(
            "rules",
            payload if isinstance(payload, list) else []
        )

        for rule in rules:
            yield path.stem.upper(), rule


def test_registry_covers_every_stage6_condition_fact():
    registry = _registry()["facts"]

    missing = []

    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            fact = condition["fact"]

            if fact not in registry:
                missing.append(
                    (
                        country,
                        rule.get("rule_id"),
                        fact,
                    )
                )

    assert missing == []


def test_registry_contains_no_unmapped_facts():
    registry = _registry()["facts"]

    assert [
        fact
        for fact, metadata in registry.items()
        if metadata["classification"] == "unmapped"
    ] == []


def test_no_numeric_direct_ownership_condition_remains():
    findings = []

    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            if (
                condition.get("fact") == "direct_ownership"
                and condition.get("operator")
                in {">", ">=", "<", "<="}
            ):
                findings.append(
                    (
                        country,
                        rule.get("rule_id"),
                        condition,
                    )
                )

    assert findings == []


def test_percentage_ownership_conditions_use_numeric_fact():
    invalid = []

    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            if (
                condition.get("operator")
                in {">", ">=", "<", "<="}
                and condition.get("fact")
                == "direct_ownership"
            ):
                invalid.append(
                    (
                        country,
                        rule.get("rule_id"),
                        condition,
                    )
                )

    assert invalid == []


def test_treaty_specific_conditions_never_fall_into_standard_input():
    registry = _registry()["facts"]

    explicit_treaty_specific = {
        "article_11_3_exemption",
        "article_11_3a_exemption",
        "special_article_11_3_exemption",
        "recipient_or_financing",
        "recipient_or_loan_provider_or_guarantor",
        "loan_or_credit_provider",
        "loan_provider",
        "lender_category",
        "borrower_category",
        "loan_is_noncommercial",
        "minimum_term_years",
        "official_foreign_exchange_reserve_investment",
        "purpose",
        "qualifying_article_11_2a_case",
        "canadian_non_resident_owned_investment_corporation_exception",
        "continuous_holding_period_days",
        "holding_period_years",
        "recipient_has_immediate_entitlement",
        "recipient_is_partnership",
        "voting_ownership",
        "voting_power_control",
    }

    for fact in explicit_treaty_specific:
        if fact in registry:
            assert (
                registry[fact]["classification"]
                == "treaty_specific_structured"
            )


def test_minimum_ownership_legacy_fact_is_fully_migrated():
    findings = []

    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            if condition.get("fact") == "minimum_ownership":
                findings.append(
                    (
                        country,
                        rule.get("rule_id"),
                        condition,
                    )
                )

    assert findings == []


def test_pe_connection_inverse_facts_are_derived():
    registry = _registry()["facts"]

    expected = {
        "claim_not_effectively_connected_to_czech_pe",
        "right_or_property_not_effectively_connected_to_czech_pe_or_fixed_base",
    }

    for fact in expected:
        assert fact in registry
        assert registry[fact]["classification"] == "derived"
