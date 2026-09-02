from __future__ import annotations

import json
from pathlib import Path

from taxtreat.services.intake import build_intake_plan
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC = ROOT / "data/legal_reviews/sk_outbound/treaty_semantic_candidates.json"
ARTICLES = ROOT / "data/legal_reviews/sk_outbound/treaty_article_machine_extraction.json"
INDUSTRIAL = "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
EN_DYNAMIC_INTAKE = ROOT / "app/web/workspace-dynamic-intake-en-20260830.js"


def _generated_royalty_rows(countries: list[str] | None = None) -> dict[str, list[dict]]:
    """Run the production builder parser out-of-process.

    Keeping the very large materializer out of the pytest process prevents an
    import-only coverage penalty while still exercising the exact production
    royalty_branches implementation against the repository's real datasets.
    """
    script = r'''
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
    if requested and country not in requested:
        continue
    result[country] = royalty_branches(scope, article_by_country[country]) or []
print(json.dumps(result, ensure_ascii=False))
'''
    requested = countries or []
    completed = subprocess.run(
        [sys.executable, "-c", script, json.dumps(requested)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def _royalty_rows(country: str) -> list[dict]:
    return _generated_royalty_rows([country])[country]

def test_vn_industrial_ip_requires_secondary_subcategory_and_has_no_broad_conflict():
    rows = _royalty_rows("VN")
    industrial = [
        row
        for row in rows
        if any(
            condition.get("fact") == "royalty_category"
            and condition.get("value") == INDUSTRIAL
            for condition in row["conditions"]
        )
    ]

    assert {row["rate"] for row in industrial} == {5.0, 10.0}
    assert all(
        any(
            condition.get("fact") == "royalty_industrial_ip_subcategory"
            for condition in row["conditions"]
        )
        for row in industrial
    )

    by_signature = {}
    for row in industrial:
        signature = json.dumps(row["conditions"], sort_keys=True)
        by_signature.setdefault(signature, set()).add(row["rate"])
    assert all(len(rates) == 1 for rates in by_signature.values())


def test_br_trademark_is_25_and_other_industrial_ip_is_15():
    rows = _royalty_rows("BR")
    trademark = next(row for row in rows if row["suffix"] == "ROYALTY-BR-TRADEMARK-25")
    other = next(row for row in rows if row["suffix"] == "ROYALTY-BR-OTHER-INDUSTRIAL-IP-15")

    assert trademark["rate"] == 25.0
    assert trademark["conditions"][-1] == {
        "fact": "royalty_industrial_ip_subcategory",
        "fact_source": "transaction",
        "operator": "==",
        "value": "trademark",
    }
    assert other["rate"] == 15.0
    assert set(other["conditions"][-1]["value"]) == {
        "patent_design_model_plan_secret_formula_or_process",
        "industrial_or_scientific_knowhow",
        "commercial_knowhow",
    }


def test_tn_technical_study_or_assistance_is_explicit_15_percent_branch():
    rows = _royalty_rows("TN")
    row = next(
        row
        for row in rows
        if row["suffix"] == "ROYALTY-TN-TECHNICAL-STUDY-OR-ASSISTANCE-15"
    )
    assert row["rate"] == 15.0
    assert any(
        condition.get("fact")
        == "royalty_is_technical_or_economic_study_or_technical_assistance"
        and condition.get("value") is True
        for condition in row["conditions"]
    )


def test_by_other_category_requires_transport_vehicle_confirmation():
    rows = _royalty_rows("BY")
    other = [
        row
        for row in rows
        if any(
            condition.get("fact") == "royalty_category"
            and condition.get("value") == "other"
            for condition in row["conditions"]
        )
    ]
    assert len(other) == 1
    assert other[0]["rate"] == 10.0
    assert any(
        condition.get("fact") == "royalty_is_transport_vehicle"
        and condition.get("value") is True
        for condition in other[0]["conditions"]
    )


def _question(fact: str) -> dict:
    plan = build_intake_plan(
        {
            "source_country": "SK",
            "recipient_country": "VN",
            "income_type": "royalty",
        },
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": [fact],
        },
    )
    assert plan["questions"]
    return plan["questions"][0]


def test_secondary_royalty_discriminator_is_client_answerable_choice():
    question = _question("royalty_industrial_ip_subcategory")
    assert question["client_answerable"] is True
    assert question["response_type"] == "choice"
    assert len(question["options"]) == 4


def test_tn_and_by_secondary_facts_are_client_answerable_booleans():
    for fact in (
        "royalty_is_transport_vehicle",
        "royalty_is_technical_or_economic_study_or_technical_assistance",
        "software_classified_as_article_12_3a_copyright",
        "royalty_is_waiver",
    ):
        question = _question(fact)
        assert question["client_answerable"] is True
        assert question["response_type"] == "boolean"


def test_all_75_sk_royalty_builds_have_no_same_fact_signature_with_different_outcomes():
    built = _generated_royalty_rows()
    assert len(built) == 75

    conflicts = []
    for country, rows in sorted(built.items()):
        by_signature = {}
        for row in rows:
            signature = json.dumps(row["conditions"], sort_keys=True)
            outcome = (row.get("rate"), row.get("tax_treatment"))
            by_signature.setdefault(signature, set()).add(outcome)
        for signature, outcomes in by_signature.items():
            if len(outcomes) > 1:
                conflicts.append((country, json.loads(signature), sorted(map(str, outcomes))))

    assert conflicts == []

def test_new_royalty_follow_up_questions_are_localized_in_english_ui():
    text = EN_DYNAMIC_INTAKE.read_text(encoding="utf-8")
    for fact in (
        "royalty_industrial_ip_subcategory",
        "royalty_is_transport_vehicle",
        "royalty_is_technical_or_economic_study_or_technical_assistance",
        "software_classified_as_article_12_3a_copyright",
        "royalty_is_waiver",
    ):
        assert fact in text
    for value in (
        "patent_design_model_plan_secret_formula_or_process",
        "trademark",
        "industrial_or_scientific_knowhow",
        "commercial_knowhow",
    ):
        assert value in text
