from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


def request(**overrides):
    values = {
        "source_country": "CZ",
        "recipient_country": "CH",
        "income_type": "royalties",
        "transaction_date": date(2026, 8, 3),
        "facts": {
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
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


def test_canonical_decision_returns_out_of_scope_explicitly():
    unsupported_country = analyze_transaction(
        request(recipient_country="DE")
    )
    unsupported_income = analyze_transaction(
        request(income_type="service_fee")
    )

    assert unsupported_country.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_country.requires_review is False
    assert unsupported_income.status == DecisionStatus.OUT_OF_SCOPE
    assert unsupported_income.requires_review is False


def test_canonical_decision_without_legal_fact_condition_still_uses_rule_gate():
    result = analyze_transaction(
        request(
            recipient_country="AT",
            income_type="interest",
            facts={
                "beneficial_owner": True,
                "permanent_establishment_connection": False,
            },
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == []
