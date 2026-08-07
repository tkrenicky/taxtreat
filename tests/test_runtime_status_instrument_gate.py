from datetime import date

from taxtreat.services.runtime_gate import evaluate_runtime_gate


COMMON = {
    "recipient_legal_form": "company",
    "beneficial_owner": True,
    "anti_abuse_review_passed": True,
    "residence_certificate_available": True,
}


def test_belarus_dividend_blocked_during_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="dividend",
        transaction_date=date(2026, 8, 7),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is False
    assert result.missing_facts == []
    assert "suspended" in result.explanation.lower()


def test_belarus_interest_blocked_during_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="interest",
        transaction_date=date(2026, 8, 7),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is False
    assert result.missing_facts == []
    assert "suspended" in result.explanation.lower()


def test_belarus_dividend_not_status_blocked_before_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="dividend",
        transaction_date=date(2024, 5, 31),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is False
    assert "ownership_percent" in result.missing_facts


def test_belarus_dividend_not_status_blocked_after_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="dividend",
        transaction_date=date(2027, 1, 1),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is False
    assert "ownership_percent" in result.missing_facts


def test_belarus_royalty_not_blocked_by_status_notice():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="royalty",
        transaction_date=date(2026, 8, 7),
        facts={
            **COMMON,
            "royalty_classification": "copyright",
        },
    )

    assert result.applies is True
    assert result.allowed is True


def test_russia_still_blocked_by_status_dataset():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RU",
        income_type="interest",
        transaction_date=date(2026, 8, 7),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is False
    assert result.missing_facts == []
    assert "suspended" in result.explanation.lower()
