from datetime import date

from taxtreat.services.runtime_gate import evaluate_runtime_gate


COMMON = {
    "recipient_legal_form": "company",
    "beneficial_owner": True,
    "anti_abuse_review_passed": True,
    "residence_certificate_available": True,
}


def test_dividend_requires_income_specific_facts():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="dividend",
        transaction_date=date(2024, 5, 31),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is True
    assert result.missing_facts == []


def test_dividend_passes_income_specific_gate():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="dividend",
        transaction_date=date(2024, 5, 31),
        facts={
            **COMMON,
            "ownership_percent": 100,
            "holding_period_months": 24,
            "recipient_is_qualifying_company": True,
        },
    )

    assert result.applies is True
    assert result.allowed is True


def test_interest_requires_related_party_status():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RS",
        income_type="interest",
        transaction_date=date(2026, 1, 15),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is True
    assert result.missing_facts == []


def test_interest_passes_income_specific_gate():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RS",
        income_type="interest",
        transaction_date=date(2026, 1, 15),
        facts={
            **COMMON,
            "related_party_status": False,
        },
    )

    assert result.applies is True
    assert result.allowed is True


def test_royalty_requires_classification():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="royalty",
        transaction_date=date(2026, 1, 15),
        facts=COMMON,
    )

    assert result.applies is True
    assert result.allowed is True
    assert result.missing_facts == []


def test_royalty_passes_income_specific_gate():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="royalty",
        transaction_date=date(2026, 1, 15),
        facts={
            **COMMON,
            "royalty_classification": "copyright",
        },
    )

    assert result.applies is True
    assert result.allowed is True
