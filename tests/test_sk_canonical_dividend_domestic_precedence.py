from __future__ import annotations

from datetime import date

import taxtreat.services.decision as decision_service
from taxtreat.countries.sk import evaluate_domestic_precedence
from taxtreat.engine.legal_rule_engine import DecisionStatus, TaxTreatment
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)
from taxtreat.services.runtime_gate import RuntimeGateResult


def _request(**fact_overrides):
    facts = {
        "recipient_entity_type": "corporate",
        "distribution_is_tax_deductible_for_payer": False,
        "recipient_is_non_cooperating_state_taxpayer": False,
        "distribution_category_is_section_3_1_f": False,
    }
    facts.update(fact_overrides)

    return CanonicalAnalysisRequest(
        source_country="SK",
        recipient_country="CZ",
        income_type="dividend",
        transaction_date=date(2026, 8, 21),
        facts=facts,
    )


def test_sk_domestic_legal_result_is_outside_subject_non_rate():
    result = evaluate_domestic_precedence(recipient_country=_request().recipient_country, income_type=_request().income_type, transaction_date=_request().transaction_date, facts=_request().facts)

    assert result is not None
    assert result.status == DecisionStatus.FINAL
    assert result.requires_review is False
    assert result.eligible is True

    assert result.selected_rule_id == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    assert result.tax_treatment == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX

    # Outside subject is N/A, not a literal 0% rate.
    assert result.rate is None
    assert result.candidate_rate is None

    assert result.applied_rule_ids == [
        "SK-DIV-DOMESTIC-SECTION-12-7-C"
    ]


def test_canonical_sk_result_is_final_after_release_reconfirmation():
    result = analyze_transaction(_request())

    assert result.status == DecisionStatus.FINAL
    assert result.requires_review is False
    assert result.eligible is True

    assert result.rate is None
    assert (
        result.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert (
        result.selected_rule_id
        == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    )

def test_domestic_outside_subject_still_bypasses_treaty_runtime_gate(
    monkeypatch,
):
    def fail_if_called(**kwargs):
        raise AssertionError(
            "Treaty/runtime gate must not run after domestic "
            "outside-subject determination."
        )

    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        fail_if_called,
    )

    result = analyze_transaction(_request())

    assert result.status == DecisionStatus.FINAL
    assert result.requires_review is False
    assert result.eligible is True
    assert result.rate is None
    assert (
        result.tax_treatment
        == TaxTreatment.OUTSIDE_SUBJECT_OF_TAX
    )
    assert (
        result.selected_rule_id
        == "SK-DIV-DOMESTIC-SECTION-12-7-C"
    )

def test_missing_domestic_fact_is_fail_closed_before_treaty_analysis(
    monkeypatch,
):
    request = _request()
    facts = dict(request.facts)
    facts.pop("distribution_is_tax_deductible_for_payer")

    def fail_if_called(**kwargs):
        raise AssertionError(
            "Treaty/runtime gate must not run while SK domestic facts "
            "are unresolved."
        )

    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        fail_if_called,
    )

    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="CZ",
            income_type="dividend",
            transaction_date=date(2026, 8, 21),
            facts=facts,
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.tax_treatment is None
    assert result.missing_facts == [
        "distribution_is_tax_deductible_for_payer"
    ]

    # This is a substantive missing-fact block, not merely release status.
    assert result.missing_legal_layers == []


def test_non_cooperating_state_exception_continues_to_taxable_branch(
    monkeypatch,
):
    calls = []

    def blocked_gate(**kwargs):
        calls.append(kwargs)
        return RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=["taxable_domestic_branch"],
            explanation="Domestic taxable branch requires further analysis.",
        )

    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        blocked_gate,
    )

    result = analyze_transaction(
        _request(recipient_is_non_cooperating_state_taxpayer=True)
    )

    assert calls
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.candidate_rule_id is None
    assert result.tax_treatment is None


def test_deductible_distribution_continues_to_taxable_branch(
    monkeypatch,
):
    calls = []

    def blocked_gate(**kwargs):
        calls.append(kwargs)
        return RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=["taxable_domestic_branch"],
            explanation="Domestic taxable branch requires further analysis.",
        )

    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        blocked_gate,
    )

    result = analyze_transaction(
        _request(distribution_is_tax_deductible_for_payer=True)
    )

    assert calls
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.tax_treatment is None


def test_section_3_1_f_distribution_continues_to_taxable_branch(
    monkeypatch,
):
    calls = []

    def blocked_gate(**kwargs):
        calls.append(kwargs)
        return RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=["taxable_domestic_branch"],
            explanation="Domestic taxable branch requires further analysis.",
        )

    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        blocked_gate,
    )

    result = analyze_transaction(
        _request(distribution_category_is_section_3_1_f=True)
    )

    assert calls
    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.tax_treatment is None


def test_sk_domestic_candidate_carries_only_slovak_primary_source():
    result = evaluate_domestic_precedence(recipient_country=_request().recipient_country, income_type=_request().income_type, transaction_date=_request().transaction_date, facts=_request().facts)

    assert result is not None
    assert len(result.citations) == 1

    citation = result.citations[0]

    assert citation["legal_layer"] == "domestic"
    assert "595/2003" in citation["legal_instrument"]
    assert "slov-lex.sk" in citation["source_url"]
    assert citation["rate"] is None

    assert "CZ" not in result.selected_rule_id
