from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "sk_outbound"
    / "dividend_domestic_condition_model.json"
)


def _load() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def test_sk_corporate_dividend_uses_outside_subject_rule_not_czech_exemption():
    payload = _load()

    assert payload["source_country"] == "SK"
    assert payload["income_type"] == "dividend"
    assert payload["recipient_scope"] == "corporate_recipient"
    assert payload["primary_rule"]["legal_reference"] == "§ 12 ods. 7 písm. c)"
    assert payload["primary_rule"]["treatment"] == (
        "outside_subject_of_corporate_income_tax_candidate"
    )
    assert payload["policy"][
        "slovak_domestic_law_is_independent_from_czech_parent_subsidiary_rules"
    ] is True


def test_sk_dividend_model_requires_deductibility_and_non_cooperating_state_facts():
    payload = _load()
    required = set(payload["required_transaction_facts"])

    assert "distribution_is_tax_deductible_for_payer" in required
    assert "recipient_is_non_cooperating_state_taxpayer" in required
    assert "distribution_category_is_section_3_1_f" in required

    exceptions = {row["exception_id"]: row for row in payload["exceptions"]}
    assert exceptions["non_cooperating_state_legal_entity"]["machine_status"] == (
        "blocked_until_official_2026_cooperating_state_list_body_is_ingested"
    )
    assert exceptions["payer_deductible_distribution"]["machine_status"] == (
        "transaction_fact_required"
    )


def test_sk_dividend_model_uses_2026_statutory_version_and_remains_fail_closed():
    payload = _load()

    assert payload["law_effective_from"] == "2026-01-01"
    assert payload["law_effective_to"] == "2026-12-30"
    source = payload["primary_sources"][0]
    assert source["url"].endswith("/20260101.print.html")
    assert source["effective_from"] == "2026-01-01"
    assert source["effective_to"] == "2026-12-30"

    assert payload["human_review_status"] == "not_started"
    assert payload["approval_eligible"] is False
    assert payload["production_released"] is False
    assert payload["policy"]["runtime_release"] is False
