from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "data/legal_rules_sk/om.json"


def _generated_rows() -> list[dict]:
    script = r"""
import json
from pathlib import Path
from taxtreat.tools.build_sk_structured_treaty_rules import (
    _merge_royalty_source_conditions,
    royalty_branches,
)

root = Path.cwd()
semantic = json.loads(
    (root / "data/legal_reviews/sk_outbound/treaty_semantic_candidates.json")
    .read_text(encoding="utf-8")
)
articles = json.loads(
    (root / "data/legal_reviews/sk_outbound/treaty_article_machine_extraction.json")
    .read_text(encoding="utf-8")
)
scope = next(
    row for row in semantic["scopes"]
    if row["recipient_country"] == "OM" and row["income_type"] == "royalty"
)
article = next(
    row for row in articles["scopes"]
    if row["recipient_country"] == "OM" and row["income_type"] == "royalty"
)
rows = royalty_branches(scope, article) or []
for row in rows:
    row["conditions"] = _merge_royalty_source_conditions(
        row["conditions"], scope, article
    )
print(json.dumps(rows, ensure_ascii=False))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _condition(row: dict, fact: str) -> dict | None:
    return next(
        (condition for condition in row["conditions"] if condition.get("fact") == fact),
        None,
    )


def test_oman_builder_requires_both_special_legal_determinations():
    rows = _generated_rows()
    assert len(rows) == 1

    row = rows[0]
    assert row["rate"] == 10.0
    assert row["suffix"] == "ROYALTY-OM-SOURCE-10-SPECIAL-CONDITIONS"
    assert _condition(row, "permanent_establishment_connection") == {
        "fact": "permanent_establishment_connection",
        "fact_source": "transaction",
        "operator": "==",
        "value": False,
    }
    assert _condition(row, "om_royalty_connected_to_article_7_1_c_activity") == {
        "fact": "om_royalty_connected_to_article_7_1_c_activity",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }
    assert _condition(row, "om_royalty_main_purpose_abuse") == {
        "fact": "om_royalty_main_purpose_abuse",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }


def test_oman_static_runtime_is_not_simple_and_matches_builder_conditions():
    payload = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    rows = [
        row for row in payload["rules"]
        if row["income_type"] == "royalty" and row["legal_layer"] == "treaty"
    ]

    assert len(rows) == 1
    row = rows[0]
    assert "SIMPLE-1" not in row["rule_id"]
    assert row["rule_id"] == (
        "SK-OM-ROYALTY-TREATY-ROYALTY-OM-SOURCE-10-SPECIAL-CONDITIONS"
    )
    assert row["rate"] == 10.0
    assert _condition(row, "om_royalty_connected_to_article_7_1_c_activity")["value"] is False
    assert _condition(row, "om_royalty_main_purpose_abuse")["value"] is False


def test_oman_source_text_contains_both_guarded_treaty_conditions():
    payload = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    row = next(
        row for row in payload["rules"]
        if row["income_type"] == "royalty" and row["legal_layer"] == "treaty"
    )
    text = row["source_text"].lower()

    assert "článku 7 ods. 1 písm. c)" in text
    assert "hlavným účelom alebo jedným z hlavných účelov" in text
    assert "bolo zneužitie tohto článku" in text
