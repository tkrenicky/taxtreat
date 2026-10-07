from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"


def _generated_rows(countries: list[str]) -> dict[str, list[dict]]:
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
wanted = set(json.loads(__import__("sys").argv[1]))
article_by_country = {
    row["recipient_country"]: row
    for row in articles["scopes"]
    if row["income_type"] == "royalty"
}
result = {}
for scope in semantic["scopes"]:
    if scope["income_type"] != "royalty":
        continue
    country = scope["recipient_country"]
    if country not in wanted:
        continue
    article = article_by_country[country]
    rows = royalty_branches(scope, article) or []
    for row in rows:
        row["conditions"] = _merge_royalty_source_conditions(
            row["conditions"], scope, article
        )
    result[country] = rows
print(json.dumps(result, ensure_ascii=False))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, json.dumps(countries)],
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


def _static_rows(country: str) -> list[dict]:
    payload = json.loads(
        (RULE_DIR / f"{country.lower()}.json").read_text(encoding="utf-8")
    )
    return [
        row for row in payload["rules"]
        if row["income_type"] == "royalty" and row["legal_layer"] == "treaty"
    ]


def test_id_and_vn_builder_require_article_7_1_c_connection_to_be_false():
    built = _generated_rows(["ID", "VN"])
    assert set(built) == {"ID", "VN"}
    assert len(built["ID"]) == 8
    assert len(built["VN"]) == 8

    expected = {
        "fact": "royalty_connected_to_article_7_1_c_activity",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }
    for country in ("ID", "VN"):
        assert all(
            _condition(row, "royalty_connected_to_article_7_1_c_activity")
            == expected
            for row in built[country]
        )


def test_id_and_vn_static_runtime_preserve_article_7_1_c_guard():
    expected = {
        "fact": "royalty_connected_to_article_7_1_c_activity",
        "fact_source": "determination",
        "operator": "==",
        "value": False,
    }
    for country in ("ID", "VN"):
        rows = _static_rows(country)
        assert len(rows) == 8
        assert all(
            _condition(row, "royalty_connected_to_article_7_1_c_activity")
            == expected
            for row in rows
        )


def test_id_and_vn_source_text_supports_article_7_1_c_guard():
    for country in ("ID", "VN"):
        row = _static_rows(country)[0]
        text = row["source_text"].lower()
        assert "článku 7 ods. 1 písm. c)" in text
        assert (
            "obchodné činnosti uvedené v článku 7 ods. 1 písm. c)" in text
            or "podnikateľské činnosti uvedené v článku 7 ods. 1 písm. c)" in text
        )


def test_audit_records_article_7_1_c_discriminator_for_id_and_vn():
    from taxtreat.tools.audit_sk_royalty_categories import (
        KNOWN_ADDITIONAL_DISCRIMINATORS,
    )

    assert "article_7_1_c_business_activity_connection" in (
        KNOWN_ADDITIONAL_DISCRIMINATORS["ID"]
    )
    assert "article_7_1_c_business_activity_connection" in (
        KNOWN_ADDITIONAL_DISCRIMINATORS["VN"]
    )
