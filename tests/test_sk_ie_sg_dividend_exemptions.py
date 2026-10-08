from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"


def _built() -> dict:
    script = r"""
import json
from pathlib import Path
from taxtreat.tools.build_sk_structured_treaty_rules import (
    dividend_branches,
    dividend_requires_explicit_branch,
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
result = {}
for country in ("IE", "SG"):
    scope = next(
        row for row in semantic["scopes"]
        if row["recipient_country"] == country and row["income_type"] == "dividend"
    )
    article = next(
        row for row in articles["scopes"]
        if row["recipient_country"] == country and row["income_type"] == "dividend"
    )
    result[country] = {
        "rows": dividend_branches(scope, article),
        "required": dividend_requires_explicit_branch(scope),
    }
print(json.dumps(result, ensure_ascii=False))
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


def _static(country: str) -> list[dict]:
    payload = json.loads(
        (RULE_DIR / f"{country.lower()}.json").read_text(encoding="utf-8")
    )
    return [
        row for row in payload["rules"]
        if row["income_type"] == "dividend" and row["legal_layer"] == "treaty"
    ]


def test_ie_dividend_exemption_is_explicit_and_fail_closed():
    built = _built()["IE"]
    assert built["required"] is True
    rows = built["rows"]
    assert [row["rate"] for row in rows] == [0.0, 10.0]
    assert _condition(rows[0], "ie_dividend_direct_25_voting_exemption")["value"] is True
    assert _condition(rows[1], "ie_dividend_direct_25_voting_exemption")["value"] is False
    assert rows[0]["tax_treatment"] == "exclusive_foreign_taxation"

    static = _static("IE")
    assert len(static) == 2
    assert {row["rate"] for row in static} == {0, 10}
    assert all(
        _condition(row, "ie_dividend_direct_25_voting_exemption") is not None
        for row in static
    )


def test_sg_government_exemption_is_explicit_and_ordinary_rates_require_false():
    built = _built()["SG"]
    assert built["required"] is True
    rows = built["rows"]
    assert [row["rate"] for row in rows] == [0.0, 5.0, 10.0]
    assert _condition(rows[0], "sg_dividend_recipient_is_treaty_government")["value"] is True
    assert rows[0]["tax_treatment"] == "exclusive_foreign_taxation"
    assert all(
        _condition(row, "sg_dividend_recipient_is_treaty_government")["value"] is False
        for row in rows[1:]
    )

    static = _static("SG")
    assert len(static) == 3
    assert {row["rate"] for row in static} == {0, 5, 10}
    ordinary = [row for row in static if row["rate"] in {5, 10}]
    assert all(
        _condition(row, "sg_dividend_recipient_is_treaty_government")["value"] is False
        for row in ordinary
    )


def test_summary_tracks_three_dividend_special_condition_scopes():
    summary = json.loads(
        (ROOT / "data/legal_reviews/sk_outbound/structured_treaty_rule_materialization_summary.json")
        .read_text(encoding="utf-8")
    )
    modes = summary["materialization_modes"]
    assert modes["source_text_dividend_special_conditions"] == 3
    assert modes["simple_single_rate"] == 86
    assert modes["source_text_dividend_branch_pair"] == 42
