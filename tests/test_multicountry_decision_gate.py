from datetime import date

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


def test_registered_released_sk_dividend_uses_domestic_first_gate():
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
    assert result.missing_legal_layers == []
    assert result.missing_facts == [
        "distribution_category_is_section_3_1_f",
        "distribution_is_tax_deductible_for_payer",
        "recipient_entity_type",
        "recipient_is_non_cooperating_state_taxpayer",
    ]
