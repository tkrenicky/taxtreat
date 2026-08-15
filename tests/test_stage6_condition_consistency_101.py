from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import (
    _boolean_like,
    _numeric_like,
)


RULE_DIR = Path("data/legal_rules_stage6")


def _rules():
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 101

    for path in files:
        payload = json.loads(path.read_text())
        rules = (
            payload.get("rules", [])
            if isinstance(payload, dict)
            else payload
        )
        for rule in rules:
            yield path.stem.upper(), rule


def test_exactly_101_stage6_country_packages_exist():
    assert len(list(RULE_DIR.glob("*.json"))) == 101


def test_all_boolean_string_conditions_are_engine_normalizable():
    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            value = condition.get("value")

            if (
                condition.get("operator") in {"==", "!="}
                and isinstance(value, str)
                and value.strip().lower()
                in {"true", "false", "yes", "no", "1", "0"}
            ):
                assert _boolean_like(value) is not None, (
                    country,
                    rule.get("rule_id"),
                    condition,
                )


def test_all_numeric_string_thresholds_are_engine_normalizable():
    for country, rule in _rules():
        for condition in rule.get("conditions", []):
            operator = condition.get("operator")
            value = condition.get("value")

            if operator not in {">", ">=", "<", "<="}:
                continue

            if not isinstance(value, str):
                continue

            normalized = value.strip().rstrip("%").strip()

            try:
                float(normalized)
            except ValueError:
                continue

            assert _numeric_like(value) is not None, (
                country,
                rule.get("rule_id"),
                condition,
            )


def test_direct_ownership_is_never_silently_treated_as_numeric_boolean():
    """
    direct_ownership sent by Stage 7B is a boolean.

    Legacy Stage 6 rules that use direct_ownership with a percentage
    threshold must remain visible as a data-model finding until migrated
    to explicit ownership_percent + direct_ownership semantics.
    """
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
                        condition.get("value"),
                    )
                )

    # Legacy model migrated:
    # directness is boolean, threshold uses ownership_percent.
    assert findings == []
