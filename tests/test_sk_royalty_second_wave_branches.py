from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"

COPYRIGHT = "copyright_literary_artistic_scientific_nonfilm_nonsoftware"
FILM = "cinematographic_films_or_broadcast_media"
INDUSTRIAL = "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
EQUIPMENT_FINANCIAL = "financial_lease_of_equipment"
EQUIPMENT_OPERATING = "operating_lease_or_other_use_of_equipment"


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
requested = set(json.loads(__import__("sys").argv[1]))
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
    if country not in requested:
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


def test_second_wave_builder_eliminates_simple_fallback_for_all_six_countries():
    countries = ["AE", "FR", "JP", "LK", "LU", "SE"]
    built = _generated_rows(countries)
    assert set(built) == set(countries)
    assert all(len(built[country]) > 1 for country in countries)


def test_fr_jp_lu_se_split_copyright_from_industrial_and_equipment():
    built = _generated_rows(["FR", "JP", "LU", "SE"])
    expected_rate = {"FR": 5.0, "JP": 10.0, "LU": 10.0, "SE": 5.0}

    for country, rows in built.items():
        by_category = {
            _condition(row, "royalty_category")["value"]: row
            for row in rows
        }
        assert by_category[COPYRIGHT]["rate"] == 0.0
        assert by_category[COPYRIGHT]["tax_treatment"] == "exclusive_foreign_taxation"
        assert by_category[FILM]["rate"] == 0.0
        assert by_category[FILM]["tax_treatment"] == "exclusive_foreign_taxation"
        for category in (INDUSTRIAL, EQUIPMENT_FINANCIAL, EQUIPMENT_OPERATING):
            assert by_category[category]["rate"] == expected_rate[country]
        assert all(
            _condition(row, "permanent_establishment_connection")["value"] is False
            for row in rows
        )


def test_lk_industrial_ip_is_narrowed_to_source_text_supported_subcategories():
    rows = _generated_rows(["LK"])["LK"]
    copyright_rows = [
        row for row in rows
        if _condition(row, "royalty_category")
        and _condition(row, "royalty_category")["value"] in {COPYRIGHT, FILM}
    ]
    assert len(copyright_rows) == 2
    assert all(row["rate"] == 0.0 for row in copyright_rows)

    industrial_rows = [
        row for row in rows
        if _condition(row, "royalty_category")
        and _condition(row, "royalty_category")["value"] == INDUSTRIAL
    ]
    assert len(industrial_rows) == 2
    assert {
        _condition(row, "royalty_industrial_ip_subcategory")["value"]
        for row in industrial_rows
    } == {
        "patent_design_model_plan_secret_formula_or_process",
        "trademark",
    }
    assert all(row["rate"] == 10.0 for row in industrial_rows)
    assert all(
        _condition(row, "royalty_industrial_ip_subcategory")["value"]
        not in {"industrial_or_scientific_knowhow", "commercial_knowhow"}
        for row in industrial_rows
    )


def test_ae_public_institution_exemption_is_a_determination_not_a_simple_rate():
    rows = _generated_rows(["AE"])["AE"]
    assert len(rows) == 2

    exempt = next(row for row in rows if row["rate"] == 0.0)
    ordinary = next(row for row in rows if row["rate"] == 10.0)

    assert exempt["tax_treatment"] == "exclusive_foreign_taxation"
    assert _condition(exempt, "ae_royalty_public_institution_exemption") == {
        "fact": "ae_royalty_public_institution_exemption",
        "fact_source": "determination",
        "operator": "==",
        "value": True,
    }
    assert _condition(ordinary, "ae_royalty_public_institution_exemption")["value"] is False


def test_static_runtime_second_wave_matches_explicit_branch_policy():
    for country in ("AE", "FR", "JP", "LK", "LU", "SE"):
        rows = _static_rows(country)
        assert rows
        assert all("SIMPLE-1" not in row["rule_id"] for row in rows)
        assert all("UNRESOLVED" not in row["rule_id"] for row in rows)

    assert any(
        row["rule_id"] == "SK-AE-ROYALTY-TREATY-ROYALTY-AE-PUBLIC-INSTITUTION-EXEMPT"
        for row in _static_rows("AE")
    )
    assert any(
        row["rule_id"] == "SK-JP-ROYALTY-TREATY-ROYALTY-JP-COPYRIGHT-RESIDENCE-1"
        for row in _static_rows("JP")
    )


def test_all_static_sk_royalty_treaty_rules_enforce_pe_carveout():
    files = sorted(RULE_DIR.glob("*.json"))
    assert len(files) == 75

    missing = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload["rules"]:
            if row["income_type"] != "royalty" or row["legal_layer"] != "treaty":
                continue
            condition = _condition(row, "permanent_establishment_connection")
            if condition != {
                "fact": "permanent_establishment_connection",
                "fact_source": "transaction",
                "operator": "==",
                "value": False,
            }:
                missing.append((payload["country_pair"]["recipient_country"], row["rule_id"]))

    assert missing == []
