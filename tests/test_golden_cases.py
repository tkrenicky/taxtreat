import json
from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction,
)


GOLDEN_CASES = Path("data/golden_cases")


def load_cases():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(GOLDEN_CASES.glob("*.json"))
    ]


def test_golden_cases_have_valid_structure():
    cases = load_cases()
    assert cases

    ids = []
    for case in cases:
        assert case["schema_version"] == 2
        assert case["verification"]["status"] in {
            "needs_review",
            "verified",
        }
        transaction = case["transaction"]
        assert transaction["payer_country"]
        assert transaction["recipient_country"]
        assert transaction["transaction_type"] in {
            "dividends",
            "interest",
            "royalties",
        }
        date.fromisoformat(transaction["transaction_date"])

        expected = case["expected"]
        if expected["applicable_rate"] is not None:
            assert 0 <= expected["applicable_rate"] <= 100
        assert expected["article"] in {10, 11, 12}
        assert case["sources"]
        ids.append(case["case_id"])

    assert len(ids) == len(set(ids))


def test_cz_ch_royalties_case_runs_through_canonical_engine():
    case = next(
        case
        for case in load_cases()
        if case["case_id"] == "CZ-CH-ROYALTIES-001"
    )
    transaction = case["transaction"]
    result = analyze_transaction(
        CanonicalAnalysisRequest(
            source_country=transaction["payer_country"],
            recipient_country=transaction["recipient_country"],
            income_type=transaction["transaction_type"],
            transaction_date=date.fromisoformat(
                transaction["transaction_date"]
            ),
            facts=case["facts"],
        )
    )

    expected = case["expected"]
    assert result.status == DecisionStatus(expected["status"])
    assert result.rate == expected["applicable_rate"]
    assert result.eligible is expected["eligible"]
    assert result.requires_review is expected["requires_review"]
    assert result.missing_facts == expected["missing_facts"]
