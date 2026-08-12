import json
from datetime import date
from pathlib import Path

from taxtreat.engine.legal_rule_engine import DecisionStatus
from taxtreat.engine.legal_sources import load_legal_sources
from taxtreat.services.decision import (
    CanonicalAnalysisRequest,
    analyze_transaction as canonical_analyze_transaction,
)


GOLDEN_CASES = Path("data/golden_cases")

LEGACY_RULE_DIR = (
    Path(__file__).parents[1]
    / "data"
    / "legal_rules"
)


def analyze_transaction(request):
    return canonical_analyze_transaction(
        request,
        rule_dir=LEGACY_RULE_DIR,
    )


def load_cases():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(GOLDEN_CASES.glob("*.json"))
    ]


def test_golden_cases_have_valid_structure():
    cases = load_cases()
    source_ids = set(
        load_legal_sources("data/legal_sources/pilot_at_ch.json")
    )
    assert cases

    ids = []
    for case in cases:
        assert case["schema_version"] == 3
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
        if expected["candidate_rate"] is not None:
            assert 0 <= expected["candidate_rate"] <= 100
        assert expected["dataset_release"]
        assert expected["required_citation_rule_ids"]
        assert case["sources"]
        assert set(case["sources"]).issubset(source_ids)
        ids.append(case["case_id"])

    assert len(ids) == len(set(ids))


def test_all_golden_cases_run_through_canonical_engine():
    for case in load_cases():
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
                determinations=case["determinations"],
            )
        )
        expected = case["expected"]
        citation_rule_ids = {
            citation["rule_id"] for citation in result.citations
        }

        assert result.status == DecisionStatus(expected["status"]), case["case_id"]
        assert result.rate == expected["applicable_rate"], case["case_id"]
        assert result.candidate_rate == expected["candidate_rate"], case["case_id"]
        assert result.candidate_rule_id == expected["candidate_rule_id"], case["case_id"]
        assert result.requires_review is expected["requires_review"], case["case_id"]
        assert result.missing_facts == expected["missing_facts"], case["case_id"]
        assert result.dataset_release == expected["dataset_release"], case["case_id"]
        assert set(expected["required_citation_rule_ids"]).issubset(
            citation_rule_ids
        ), case["case_id"]
