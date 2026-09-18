from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from taxtreat.services.intake import build_intake_plan


ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "data/legal_rules_sk"

COPYRIGHT = "copyright_literary_artistic_scientific_nonfilm_nonsoftware"
FILM = "cinematographic_films_or_broadcast_media"
SOFTWARE = "computer_software"
INDUSTRIAL = "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
EQUIPMENT_FINANCIAL = "financial_lease_of_equipment"
EQUIPMENT_OPERATING = "operating_lease_or_other_use_of_equipment"


def _generated_rows(country: str) -> list[dict]:
    script = r"""
import json
from pathlib import Path
from taxtreat.tools.build_sk_structured_treaty_rules import royalty_branches

root = Path.cwd()
semantic = json.loads(
    (root / "data/legal_reviews/sk_outbound/treaty_semantic_candidates.json")
    .read_text(encoding="utf-8")
)
articles = json.loads(
    (root / "data/legal_reviews/sk_outbound/treaty_article_machine_extraction.json")
    .read_text(encoding="utf-8")
)
country = __import__("sys").argv[1]
scope = next(
    row for row in semantic["scopes"]
    if row["recipient_country"] == country and row["income_type"] == "royalty"
)
article = next(
    row for row in articles["scopes"]
    if row["recipient_country"] == country and row["income_type"] == "royalty"
)
print(json.dumps(royalty_branches(scope, article) or [], ensure_ascii=False))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, country],
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


def test_es_royalty_uses_explicit_copyright_and_subject_to_tax_branches():
    rows = _generated_rows("ES")
    assert len(rows) == 7

    literary = next(
        row for row in rows
        if row["suffix"] == "ROYALTY-ES-COPYRIGHT-RESIDENCE"
    )
    assert literary["rate"] == 0.0
    assert literary["tax_treatment"] == "exclusive_foreign_taxation"
    assert _condition(literary, "royalty_category")["value"] == COPYRIGHT
    assert _condition(literary, "royalty_copyright_subcategory")["value"] == (
        "literary_dramatic_musical_or_artistic_nonfilm"
    )

    scientific = next(
        row for row in rows
        if row["suffix"] == "ROYALTY-ES-SCIENTIFIC-COPYRIGHT-SOURCE-5"
    )
    assert scientific["rate"] == 5.0
    assert _condition(scientific, "royalty_copyright_subcategory")["value"] == (
        "scientific_nonfilm"
    )

    source_rows = [row for row in rows if row["rate"] == 5.0]
    assert len(source_rows) == 6
    assert all(
        _condition(row, "recipient_taxed_in_residence") == {
            "fact": "recipient_taxed_in_residence",
            "fact_source": "transaction",
            "operator": "==",
            "value": True,
        }
        for row in source_rows
    )
    assert all(
        _condition(row, "permanent_establishment_connection")["value"] is False
        for row in rows
    )
    covered = {
        _condition(row, "royalty_category")["value"]
        for row in rows
    }
    assert {COPYRIGHT, FILM, SOFTWARE, INDUSTRIAL, EQUIPMENT_FINANCIAL, EQUIPMENT_OPERATING} <= covered
    assert "other" not in covered


def test_gb_royalty_separates_residence_only_copyright_from_source_taxable_industrial_items():
    rows = _generated_rows("GB")
    assert len(rows) == 5

    by_category = {
        _condition(row, "royalty_category")["value"]: row
        for row in rows
    }
    assert by_category[COPYRIGHT]["rate"] == 0.0
    assert by_category[COPYRIGHT]["tax_treatment"] == "exclusive_foreign_taxation"
    assert by_category[FILM]["rate"] == 0.0
    assert by_category[FILM]["tax_treatment"] == "exclusive_foreign_taxation"

    for category in (INDUSTRIAL, EQUIPMENT_FINANCIAL, EQUIPMENT_OPERATING):
        assert by_category[category]["rate"] == 10.0

    assert SOFTWARE not in by_category
    assert "other" not in by_category
    assert all(
        _condition(row, "permanent_establishment_connection")["value"] is False
        for row in rows
    )


def test_static_runtime_rules_for_es_and_gb_are_explicit_not_simple():
    expected = {
        "ES": {
            "SK-ES-ROYALTY-TREATY-ROYALTY-ES-COPYRIGHT-RESIDENCE",
            "SK-ES-ROYALTY-TREATY-ROYALTY-ES-SCIENTIFIC-COPYRIGHT-SOURCE-5",
        },
        "GB": {
            "SK-GB-ROYALTY-TREATY-ROYALTY-GB-RESIDENCE-1",
            "SK-GB-ROYALTY-TREATY-ROYALTY-GB-SOURCE-10-1",
        },
    }
    for country, required in expected.items():
        payload = json.loads(
            (RULE_DIR / f"{country.lower()}.json").read_text(encoding="utf-8")
        )
        rows = [
            row for row in payload["rules"]
            if row["income_type"] == "royalty" and row["legal_layer"] == "treaty"
        ]
        assert rows
        assert all("SIMPLE-1" not in row["rule_id"] for row in rows)
        assert required <= {row["rule_id"] for row in rows}


def test_new_spain_royalty_follow_up_facts_are_client_answerable():
    plan = build_intake_plan(
        {
            "source_country": "SK",
            "recipient_country": "ES",
            "income_type": "royalty",
        },
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": [
                "recipient_taxed_in_residence",
                "royalty_copyright_subcategory",
            ],
        },
    )
    questions = {question["fact"]: question for question in plan["questions"]}

    assert questions["recipient_taxed_in_residence"]["client_answerable"] is True
    assert questions["recipient_taxed_in_residence"]["response_type"] == "boolean"
    assert questions["royalty_copyright_subcategory"]["client_answerable"] is True
    assert questions["royalty_copyright_subcategory"]["response_type"] == "choice"
    assert {
        option[0] for option in questions["royalty_copyright_subcategory"]["options"]
    } == {
        "literary_dramatic_musical_or_artistic_nonfilm",
        "scientific_nonfilm",
        "other_or_unclear",
    }
