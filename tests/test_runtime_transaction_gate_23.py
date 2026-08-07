from datetime import date

from taxtreat.services.runtime_gate import (
    evaluate_runtime_gate,
)


COMMON_FACTS = {
    "recipient_legal_form": "company",
    "beneficial_owner": True,
    "anti_abuse_review_passed": True,
    "residence_certificate_available": True,
}


def test_reviewed_pair_fails_closed_when_common_facts_missing():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="royalty",
        transaction_date=date(
            2026,
            1,
            15,
        ),
        facts={},
    )

    assert result.applies is True
    assert result.allowed is False

    assert set(
        result.missing_facts
    ) == {
        "recipient_legal_form",
        "beneficial_owner_confirmed",
        "anti_abuse_review_passed",
        "residence_certificate_available",
    }


def test_recipient_country_satisfies_residence_identity():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="BY",
        income_type="royalty",
        transaction_date=date(
            2026,
            1,
            15,
        ),
        facts=COMMON_FACTS,
    )

    assert result.applies is True
    assert result.allowed is True
    assert result.missing_facts == []


def test_beneficial_owner_alias_is_supported():
    facts = {
        **COMMON_FACTS,
        "beneficial_owner": True,
    }

    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RS",
        income_type="interest",
        transaction_date=date(
            2026,
            1,
            15,
        ),
        facts=facts,
    )

    assert result.applies is True
    assert result.allowed is True


def test_russia_is_hard_blocked_after_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RU",
        income_type="interest",
        transaction_date=date(
            2026,
            1,
            15,
        ),
        facts=COMMON_FACTS,
    )

    assert result.applies is True
    assert result.allowed is False
    assert result.missing_facts == []

    assert "suspended" in (
        result.explanation
        or ""
    ).lower()


def test_russia_not_hard_blocked_before_suspension():
    result = evaluate_runtime_gate(
        source_country="CZ",
        recipient_country="RU",
        income_type="interest",
        transaction_date=date(
            2023,
            8,
            10,
        ),
        facts=COMMON_FACTS,
    )

    assert result.applies is True
    assert result.allowed is True


def test_scope_outside_final_23_is_unchanged():
    result = evaluate_runtime_gate(
        source_country="US",
        recipient_country="CA",
        income_type="interest",
        transaction_date=date(
            2026,
            1,
            15,
        ),
        facts={},
    )

    assert result.applies is False
    assert result.allowed is True
    assert result.missing_facts == []
