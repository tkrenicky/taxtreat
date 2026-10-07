from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/legal_reviews/sk_outbound"
RULE_PATH = ROOT / "data/legal_rules_sk/om.json"


def _generated_om_dividend() -> dict:
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
scope = next(
    row for row in semantic["scopes"]
    if row["recipient_country"] == "OM" and row["income_type"] == "dividend"
)
article = next(
    row for row in articles["scopes"]
    if row["recipient_country"] == "OM" and row["income_type"] == "dividend"
)
rows = dividend_branches(scope, article)
broken_article = {
    **article,
    "article_text": article["article_text"].replace(
        "zneužitie tohto článku", "missing anti-abuse wording"
    ),
}
print(json.dumps({
    "rows": rows,
    "explicit_required": dividend_requires_explicit_branch(scope),
    "other_country_required": dividend_requires_explicit_branch(
        {**scope, "recipient_country": "AE"}
    ),
    "broken_rows": dividend_branches(scope, broken_article),
}, ensure_ascii=False))
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


def test_oman_dividend_builder_requires_main_purpose_abuse_false():
    built = _generated_om_dividend()
    rows = built["rows"]
    assert rows is not None
    assert len(rows) == 1

    row = rows[0]
    assert row["rate"] == 0.0
    assert row["tax_treatment"] == "exclusive_foreign_taxation"
    assert row["suffix"] == "DIVIDEND-OM-RESIDENCE-ONLY-MAIN-PURPOSE-GUARD"
    assert _condition(row, "om_dividend_main_purpose_abuse") == {
        "fact": "om_dividend_main_purpose_abuse",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }


def test_oman_dividend_is_hard_gated_before_generic_fallbacks():
    built = _generated_om_dividend()
    assert built["explicit_required"] is True
    assert built["other_country_required"] is False
    assert built["broken_rows"] is None


def test_oman_static_dividend_runtime_contains_main_purpose_guard():
    payload = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    rows = [
        row for row in payload["rules"]
        if row["income_type"] == "dividend" and row["legal_layer"] == "treaty"
    ]
    assert len(rows) == 1

    row = rows[0]
    assert row["rule_id"] == (
        "SK-OM-DIVIDEND-TREATY-"
        "DIVIDEND-OM-RESIDENCE-ONLY-MAIN-PURPOSE-GUARD"
    )
    assert row["rate"] == 0
    assert row["tax_treatment"] == "exclusive_foreign_taxation"
    assert _condition(row, "om_dividend_main_purpose_abuse") == {
        "fact": "om_dividend_main_purpose_abuse",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }


def test_materialization_summary_tracks_oman_dividend_special_condition():
    summary = json.loads(
        (BASE / "structured_treaty_rule_materialization_summary.json")
        .read_text(encoding="utf-8")
    )
    modes = summary["materialization_modes"]
    assert modes["source_text_dividend_special_conditions"] == 1
    assert modes["source_text_explicit_residence_only"] == 6
