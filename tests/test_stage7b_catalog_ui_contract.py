from __future__ import annotations

import json
from pathlib import Path


RULE_DIR = Path("data/legal_rules_stage6")


def test_all_101_partner_catalogs_support_data_driven_legal_display():
    paths = sorted(RULE_DIR.glob("*.json"))

    assert len(paths) == 101

    treaty_rate_rules = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["country_pair"] == {
            "source_country": "CZ",
            "recipient_country": path.stem.upper(),
        }
        for rule in payload["rules"]:
            if (
                rule["effect"] == "rate"
                and rule["legal_layer"]
                in {"treaty", "protocol", "mli"}
            ):
                treaty_rate_rules.append(rule)
                assert rule["source_url"].startswith("https://")
                assert rule["source_text"].strip()
                assert rule["article"] is not None
                assert rule["rate"] is not None
                assert isinstance(rule["conditions"], list)

    assert treaty_rate_rules


def test_rule_sequence_suffixes_are_not_semantic_contracts():
    examples = {}
    for path in sorted(RULE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for rule in payload["rules"]:
            if rule["rule_id"].endswith("CURRENT-1"):
                examples.setdefault(rule["income_type"], set()).add(
                    (rule["article"], rule["rate"])
                )

    assert any(len(values) > 1 for values in examples.values())
