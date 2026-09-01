from datetime import date

from taxtreat.engine.legal_rule_engine import LegalRule, evaluate_legal_rules


def _rule(source_country: str, recipient_country: str, income_type: str):
    return LegalRule(
        rule_id=f"{source_country}-{recipient_country}-{income_type}-TEST",
        income_type=income_type,
        source_country=source_country,
        recipient_country=recipient_country,
        legal_instrument="treaty",
        legal_layer="treaty",
        article=10,
        rate=10.0,
        verification_status="needs_review",
        effective_from=date(2020, 1, 1),
    )


def test_cz_semantic_quarantine_does_not_leak_into_sk_source_country():
    result = evaluate_legal_rules(
        [_rule("SK", "CH", "dividend")],
        {
            "source_country": "SK",
            "recipient_country": "CH",
            "income_type": "dividend",
        },
        as_of=date(2026, 9, 1),
    )

    assert not any("quarantined pending" in line for line in result.explanation)
    assert result.requires_review is True
    assert any("not verified" in line for line in result.explanation)



def test_released_cz_scope_uses_normal_verification_gate_not_quarantine():
    result = evaluate_legal_rules(
        [_rule("CZ", "CH", "dividend")],
        {
            "source_country": "CZ",
            "recipient_country": "CH",
            "income_type": "dividend",
        },
        as_of=date(2026, 9, 1),
    )

    assert not any("quarantined pending" in line for line in result.explanation)
    assert result.requires_review is True
    assert any("not verified" in line for line in result.explanation)

