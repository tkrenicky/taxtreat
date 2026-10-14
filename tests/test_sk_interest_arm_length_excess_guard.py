from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"
EXPECTED = {
    "AU", "BE", "BA", "BR", "CY", "ME", "CN", "DK", "GR", "HR", "IN",
    "IL", "JP", "ZA", "LU", "HU", "MT", "DE", "NG", "PL", "RO", "RU",
    "GB", "RS", "ES", "CH", "SE", "IT", "TN", "TR", "TM", "UA", "US",
}


def _detected_countries() -> set[str]:
    script = r"""
import json
from pathlib import Path
from taxtreat.tools.build_sk_structured_treaty_rules import (
    _interest_arm_length_excess_guard,
)

root = Path.cwd()
articles = json.loads(
    (root / "data/legal_reviews/sk_outbound/treaty_article_machine_extraction.json")
    .read_text(encoding="utf-8")
)
countries = {
    row["recipient_country"]
    for row in articles["scopes"]
    if row["income_type"] == "interest"
    and _interest_arm_length_excess_guard(row) is not None
}
print(json.dumps(sorted(countries)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return set(json.loads(completed.stdout))


def _interest_rows(country: str) -> list[dict]:
    payload = json.loads(
        (RULE_DIR / f"{country.lower()}.json").read_text(encoding="utf-8")
    )
    return [
        row for row in payload["rules"]
        if row["income_type"] == "interest" and row["legal_layer"] == "treaty"
    ]


def _guard(row: dict) -> dict | None:
    return next(
        (
            condition
            for condition in row.get("conditions", [])
            if condition.get("fact") == "interest_payment_exceeds_arm_length_amount"
        ),
        None,
    )


def test_source_text_detection_identifies_exact_arm_length_excess_set():
    assert _detected_countries() == EXPECTED


def test_all_affected_static_interest_rules_fail_closed_on_excess():
    expected_guard = {
        "fact": "interest_payment_exceeds_arm_length_amount",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }
    for country in EXPECTED:
        rows = _interest_rows(country)
        assert rows
        assert all(_guard(row) == expected_guard for row in rows)


def test_unaffected_netherlands_interest_rules_do_not_get_spurious_guard():
    rows = _interest_rows("NL")
    assert rows
    assert all(_guard(row) is None for row in rows)
