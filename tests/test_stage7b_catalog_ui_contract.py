from __future__ import annotations

import json
from pathlib import Path

from taxtreat.engine.legal_rule_engine import _evaluate_rule
from taxtreat.engine.legal_rule_loader import load_legal_rules


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
                if rule["rate"] is None:
                    assert rule.get("tax_treatment") in {
                        "domestic_rate_applies",
                        "exclusive_foreign_taxation",
                    }
                else:
                    assert isinstance(rule["rate"], (int, float))
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


def test_austrian_royalty_ui_facts_reach_each_treaty_rule():
    rules = {
        rule.rule_id: rule
        for rule in load_legal_rules(RULE_DIR / "at.json")
    }
    cases = [
        (
            "CZ-AT-ROYALTY-CURRENT-1",
            "copyright_literary_artistic_or_scientific"
        ),
        (
            "CZ-AT-ROYALTY-CURRENT-2",
            "software_patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
        ),
        (
            "CZ-AT-ROYALTY-CURRENT-2",
            "industrial_commercial_or_scientific_equipment",
        ),
    ]

    for rule_id, category in cases:
        matches, missing, failed = _evaluate_rule(
            rules[rule_id],
            {
                "beneficial_owner": True,
                "royalty_category": category,
            },
            {},
        )
        assert matches is True
        assert missing == []
        assert failed == []
