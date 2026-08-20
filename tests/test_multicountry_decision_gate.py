from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


def test_registered_released_sk_source_country_reaches_normal_scope_evaluation():
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="CZ",
            income_type="dividend",
            transaction_date=date(2026, 8, 18),
            facts={},
        )
    )

    assert result.status == DecisionStatus.OUT_OF_SCOPE
    assert result.requires_review is False
    assert result.rate is None
    assert result.eligible is False
    assert result.missing_legal_layers == []
    assert result.explanation == [
        "The requested country-income scope is not supported."
    ]
