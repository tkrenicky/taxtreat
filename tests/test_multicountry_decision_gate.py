from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


def test_registered_unreleased_sk_source_country_fails_closed():
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country="SK",
            recipient_country="CZ",
            income_type="dividend",
            transaction_date=date(2026, 8, 18),
            facts={},
        )
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.rate is None
    assert result.eligible is False
    assert result.missing_legal_layers == [
        "domestic",
        "mli",
        "treaty_or_protocol",
    ]
    assert result.explanation == [
        "SK source-country package has not been released."
    ]
