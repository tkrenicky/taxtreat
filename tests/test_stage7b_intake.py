from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from taxtreat.services.intake import (
    _question_for_missing_fact,
    build_intake_plan,
)


client = TestClient(app)


def test_beneficial_owner_is_an_explicit_adviser_assumption():
    question = _question_for_missing_fact("beneficial_owner")

    assert question["input_path"] is None
    assert question["category"] == "professional_review"
    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"
    assert "skutečným vlastníkem" in question["prompt"]
    assert "Prohlášení skutečného vlastníka příjmu" in question[
        "required_documents"
    ]


def test_numeric_question_is_precise_and_fallback_is_not_exposed():
    ownership = _question_for_missing_fact("ownership_percent")
    unknown = _question_for_missing_fact("new_future_fact")

    assert ownership["response_type"] == "decimal_percent"
    assert ownership["input_path"] == "facts.ownership_percent"
    assert "základním kapitálu českého plátce" in ownership["prompt"]
    assert unknown["response_type"] == "professional_review"
    assert unknown["client_answerable"] is False
    assert unknown["input_path"] is None
    assert "new future fact" not in unknown["prompt"].lower()
    assert unknown["required_documents"] == []


def test_determination_and_legal_fact_are_not_client_assertions():
    determination = _question_for_missing_fact(
        "determination:treaty_ppt_passed"
    )
    unknown_determination = _question_for_missing_fact(
        "determination:new_legal_test"
    )
    legal_fact = _question_for_missing_fact(
        "legal_fact:foreign_statutory_rule"
    )

    assert determination["input_path"] == (
        "determinations.treaty_ppt_passed"
    )
    assert determination["client_answerable"] is False
    assert determination["response_type"] == "reviewed_boolean"
    assert determination["required_documents"]
    assert unknown_determination["client_answerable"] is False
    assert "daňovým poradcem" in unknown_determination["prompt"]
    assert legal_fact["input_path"] is None
    assert legal_fact["category"] == "legal_evidence"
    assert legal_fact["response_type"] == "professional_review"
    assert "foreign statutory rule" not in legal_fact["prompt"].lower()


def test_client_wording_does_not_delegate_legal_conclusions():
    holding = _question_for_missing_fact("holding_period_months")
    future_holding = _question_for_missing_fact(
        "holding_period_will_reach_months"
    )
    company_form = _question_for_missing_fact(
        "recipient_is_qualifying_company_form"
    )
    corporate_tax = _question_for_missing_fact(
        "recipient_subject_to_qualifying_corporate_tax"
    )

    assert "Od jakého data" in holding["prompt"]
    assert holding["client_answerable"] is True
    assert holding["response_type"] == "date"
    assert holding["input_path"] == "derived.acquisition_date"
    assert future_holding["client_answerable"] is False
    assert company_form["client_answerable"] is False
    assert corporate_tax["client_answerable"] is False


def test_related_professional_conditions_are_collapsed_for_clients():
    plan = build_intake_plan(
        {"facts": {}, "determinations": {}},
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": [
                "recipient_is_qualifying_company_form",
                "recipient_subject_to_qualifying_corporate_tax",
                "recipient_is_parent_company",
                "recipient_is_tax_resident_in_eligible_jurisdiction",
            ],
            "withholding_tax_calculation": None,
        },
    )

    assert len(plan["questions"]) == 1
    assert plan["questions"][0]["advisor_topic"] == (
        "recipient_eligibility"
    )


def test_plan_combines_missing_facts_documents_and_optional_amount():
    plan = build_intake_plan(
        {"facts": {}, "determinations": {}},
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": [
                "beneficial_owner",
                "determination:treaty_ppt_passed",
            ],
            "withholding_tax_calculation": None,
        },
    )

    assert plan["status"] == "ACTION_REQUIRED"
    assert len(plan["questions"]) == 2
    assert plan["optional_inputs"][0]["input_path"] == (
        "transaction_amount"
    )
    assert "Prohlášení skutečného vlastníka příjmu" in plan[
        "required_documents"
    ]
    assert plan["semantics"] == {
        "client_facts_are_not_legal_approval": True,
        "unanswered_items_remain_unresolved": True,
        "legal_determinations_require_review": True,
    }


def test_plan_requests_complete_cnb_evidence_for_fx_failure():
    plan = build_intake_plan(
        {"transaction_amount": {"amount": "100", "currency": "EUR"}},
        {
            "status": "FINAL",
            "missing_facts": [],
            "withholding_tax_calculation": {
                "status": "NOT_CALCULATED",
                "reason": "exchange_rate_evidence_missing",
            },
        },
    )

    assert plan["status"] == "ACTION_REQUIRED"
    assert plan["optional_inputs"] == []
    fx = plan["questions"][0]
    assert fx["category"] == "exchange_rate_evidence"
    assert fx["response_type"] == "structured_cnb_rate"
    assert "Odkaz na zdroj kurzu ČNB" not in fx["required_documents"]
    assert "není třeba zadávat znovu" in fx["why"]


def test_final_rate_unavailable_does_not_duplicate_legal_questions():
    plan = build_intake_plan(
        {"transaction_amount": {"amount": "100", "currency": "CZK"}},
        {
            "status": "REVIEW_REQUIRED",
            "missing_facts": [],
            "withholding_tax_calculation": {
                "status": "NOT_CALCULATED",
                "reason": "final_rate_unavailable",
            },
        },
    )

    assert plan["questions"] == []
    assert plan["status"] == "PROFESSIONAL_REVIEW_REQUIRED"


def test_complete_and_out_of_scope_plan_states():
    complete = build_intake_plan(
        {"transaction_amount": {"amount": "100", "currency": "CZK"}},
        {
            "status": "FINAL",
            "missing_facts": [],
            "withholding_tax_calculation": {"status": "CALCULATED"},
        },
    )
    out_of_scope = build_intake_plan(
        {},
        {
            "status": "OUT_OF_SCOPE",
            "missing_facts": [],
        },
    )

    assert complete["status"] == "COMPLETE"
    assert out_of_scope["status"] == "OUT_OF_SCOPE"


def test_guided_intake_endpoint_uses_actual_engine_missing_facts():
    response = client.post(
        "/analysis/intake",
        json={
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
            "transaction_date": "2026-08-12",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["status"] == "REVIEW_REQUIRED"
    assert payload["intake"]["status"] == "ACTION_REQUIRED"
    assert payload["intake"]["questions"]
    assert all(
        question["question_id"]
        in payload["analysis"]["missing_facts"]
        for question in payload["intake"]["questions"]
    )
    assert payload["intake"]["semantics"][
        "client_facts_are_not_legal_approval"
    ] is True
