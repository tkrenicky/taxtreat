from __future__ import annotations

from datetime import date

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
    evaluate_legal_rules,
)


AS_OF = date(2026, 8, 28)


def _rule(
    rule_id: str,
    *,
    income_type: str,
    rate: float,
    priority: int,
    conditions: list[LegalCondition] | None = None,
    legal_layer: str = "treaty",
) -> LegalRule:
    return LegalRule(
        rule_id=rule_id,
        income_type=income_type,
        source_country="CZ",
        recipient_country="XX",
        legal_instrument="test treaty",
        legal_layer=legal_layer,
        article=10 if income_type == "dividend" else 12,
        rate=rate,
        priority=priority,
        conditions=conditions or [],
        verification_status="verified",
    )


def test_coarse_company_type_cannot_force_general_dividend_fallback():
    rules = [
        _rule(
            "special",
            income_type="dividend",
            rate=5,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="recipient_entity_type",
                    operator="==",
                    value="company_other_than_partnership",
                ),
                LegalCondition(
                    fact="ownership_percent",
                    operator=">=",
                    value=20,
                ),
            ],
        ),
        _rule(
            "fallback",
            income_type="dividend",
            rate=15,
            priority=200,
            conditions=[
                LegalCondition(
                    fact="fallback_case",
                    operator="==",
                    value="all_other_cases",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "XX",
            "recipient_entity_type": "company",
            "ownership_percent": 100,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["recipient_entity_type"]


def test_broad_royalty_value_matching_two_rates_fails_closed():
    rules = [
        _rule(
            "financial",
            income_type="royalty",
            rate=1,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="financial_lease_of_equipment",
                )
            ],
        ),
        _rule(
            "operating",
            income_type="royalty",
            rate=5,
            priority=110,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="operating_lease_of_equipment_or_computer_software",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "XX",
            "royalty_category": "industrial_commercial_or_scientific_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["royalty_category"]


def test_atomic_royalty_value_selects_one_branch():
    rules = [
        _rule(
            "financial",
            income_type="royalty",
            rate=1,
            priority=100,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="financial_lease_of_equipment",
                )
            ],
        ),
        _rule(
            "operating",
            income_type="royalty",
            rate=5,
            priority=110,
            conditions=[
                LegalCondition(
                    fact="royalty_category",
                    operator="==",
                    value="operating_lease_of_equipment_or_computer_software",
                )
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "XX",
            "royalty_category": "financial_lease_of_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 1
    assert result.selected_rule_id == "financial"


def test_advisor_only_rule_value_fact_stays_professional_review():
    from taxtreat.services.intake import _question_for_missing_fact

    question = _question_for_missing_fact(
        "special_article_11_3_exemption",
        {
            "source_country": "CZ",
            "recipient_country": "TW",
            "income_type": "interest",
            "transaction_date": "2026-08-28",
            "facts": {},
            "determinations": {},
        },
    )

    assert question["client_answerable"] is False
    assert question["response_type"] == "professional_review"
    assert question["input_path"] is None
    assert question["category"] == "professional_review"


def test_real_au_stage6_company_input_does_not_silently_select_15_percent():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/au.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "dividend",
            "source_country": "CZ",
            "recipient_country": "AU",
            "recipient_entity_type": "company",
            "ownership_percent": 100,
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert "recipient_entity_type" in result.missing_facts


def test_real_fi_stage6_broad_equipment_input_does_not_silently_select_1_percent():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/fi.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "FI",
            "beneficial_owner": True,
            "royalty_category": "industrial_commercial_or_scientific_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.rate is None
    assert result.missing_facts == ["royalty_category"]


def test_real_fi_stage6_atomic_financial_lease_selects_1_percent_treaty_rule():
    from taxtreat.engine.legal_rule_loader import load_legal_rules
    from pathlib import Path

    rules = load_legal_rules(Path("data/legal_rules_stage6/fi.json"))
    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "FI",
            "beneficial_owner": True,
            "royalty_category": "financial_lease_of_equipment",
        },
        as_of=AS_OF,
    )

    assert result.status == DecisionStatus.FINAL
    assert result.rate == 1
    assert result.selected_rule_id == "CZ-FI-ROYALTY-CURRENT-2"
