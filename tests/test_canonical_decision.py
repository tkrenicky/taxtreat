from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)
from taxtreat.services.runtime_gate import RuntimeGateResult
import taxtreat.services.decision as decision_service


def request(**overrides):
    values = {
        "source_country": "CZ",
        "recipient_country": "CH",
        "income_type": "royalties",
        "transaction_date": date(2026, 8, 3),
        "facts": {
            "recipient_is_treaty_resident": True,
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "arm_length_amount": True,
            "recipient_is_qualifying_company": False,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
        "determinations": {"treaty_ppt_passed": True},
    }
    values.update(overrides)
    return CanonicalAnalysisRequest(**values)


def test_canonical_decision_ignores_user_supplied_legal_conclusion():
    result = analyze_transaction(request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == [
        "legal_fact:recipient_country_imposes_royalty_wht_on_nonresidents"
    ]
    assert result.candidate_rate == 5.0
    assert result.candidate_rule_id == "CZ-CH-ROY-PROTOCOL-5"


def test_canonical_decision_distinguishes_pending_from_out_of_scope():
    pending_country = analyze_transaction(
        request(recipient_country="DE")
    )
    unsupported_country = analyze_transaction(
        request(recipient_country="ZZ")
    )
    unsupported_income = analyze_transaction(
        request(income_type="service_fee")
    )

    assert pending_country.status == DecisionStatus.REVIEW_REQUIRED
    assert pending_country.requires_review is True
    assert pending_country.candidate_rate is None
    assert pending_country.missing_legal_layers == [
        "domestic",
        "eu_relief",
        "mli",
        "treaty_or_protocol",
    ]
    assert unsupported_country.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_country.requires_review is False
    assert unsupported_country.requires_review is False
    assert unsupported_income.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_income.requires_review is False


def test_canonical_decision_without_legal_fact_condition_still_uses_rule_gate():
    result = analyze_transaction(
        request(
            recipient_country="AT",
            income_type="interest",
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
                "arm_length_amount": True,
                "recipient_is_qualifying_company": False,
            },
            determinations={},
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.candidate_rate == 15.0
    assert result.missing_facts == ["determination:treaty_ppt_passed"]


def test_canonical_scoped_result_can_have_no_candidate_rate():
    result = analyze_transaction(
        request(
            recipient_country="AT",
            income_type="interest",
            transaction_date=date(2021, 1, 1),
            facts={
                "recipient_is_treaty_resident": True,
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
                "arm_length_amount": True,
                "recipient_is_qualifying_company": False,
            },
            determinations={},
        )
    )

    assert result.candidate_rule_id is None
    assert result.missing_facts == ["determination:treaty_ppt_passed"]


def test_runtime_gate_block_remains_review_required(monkeypatch):
    monkeypatch.setattr(
        decision_service,
        "evaluate_runtime_gate",
        lambda **kwargs: RuntimeGateResult(
            applies=True,
            allowed=False,
            missing_facts=["official_status_instrument_effect"],
            explanation="Status-instrument effect requires legal review.",
        ),
    )

    result = analyze_transaction(request())

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.rate is None
    assert result.eligible is False
    assert result.missing_facts == ["official_status_instrument_effect"]
    assert result.explanation == [
        "Status-instrument effect requires legal review."
    ]
