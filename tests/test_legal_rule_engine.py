from datetime import date

from taxtreat.engine.legal_rule_engine import (
    DecisionStatus,
    LegalCondition,
    LegalRule,
    evaluate_legal_rules,
)


def test_legal_engine_requires_explicit_transaction_date():
    result = evaluate_legal_rules([], {})

    assert result.status == DecisionStatus.REVIEW_REQUIRED
    assert result.requires_review is True
    assert result.missing_facts == ["transaction_date"]


def rule(
    rule_id,
    *,
    income_type,
    rate=None,
    priority=100,
    conditions=None,
    effect="rate",
    effective_from=None,
    overrides_rule_id=None,
):
    return LegalRule(
        rule_id=rule_id,
        income_type=income_type,
        source_country="CZ",
        recipient_country="CH",
        legal_instrument="treaty",
        article=11 if income_type == "interest" else 12,
        paragraph="2",
        rate=rate,
        priority=priority,
        conditions=conditions or [],
        effect=effect,
        effective_from=effective_from,
        overrides_rule_id=overrides_rule_id,
        verification_status="verified",
    )


def test_interest_rate_is_selected_from_applicable_rule():
    rules = [
        rule(
            "CZ-CH-INT-BASE",
            income_type="interest",
            rate=0.0,
            conditions=[
                LegalCondition("beneficial_owner", "==", True),
                LegalCondition("permanent_establishment_connection", "==", False),
            ],
        )
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "permanent_establishment_connection": False,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is True
    assert result.requires_review is False
    assert result.rate == 0.0
    assert result.selected_rule_id == "CZ-CH-INT-BASE"


def test_pe_connection_excludes_treaty_wht_rule():
    rules = [
        rule(
            "CZ-CH-INT-PE",
            income_type="interest",
            priority=0,
            effect="exclude",
            conditions=[
                LegalCondition("permanent_establishment_connection", "==", True),
            ],
        ),
        rule(
            "CZ-CH-INT-BASE",
            income_type="interest",
            rate=0.0,
            conditions=[
                LegalCondition("beneficial_owner", "==", True),
                LegalCondition("permanent_establishment_connection", "==", False),
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "permanent_establishment_connection": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is False
    assert result.rate is None
    assert result.selected_rule_id == "CZ-CH-INT-PE"


def test_missing_material_fact_requires_review():
    rules = [
        rule(
            "CZ-CH-INT-BASE",
            income_type="interest",
            rate=0.0,
            conditions=[
                LegalCondition("beneficial_owner", "==", True),
                LegalCondition("permanent_establishment_connection", "==", False),
            ],
        )
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.missing_facts == ["permanent_establishment_connection"]


def test_royalty_category_selects_different_rates():
    rules = [
        rule(
            "CZ-AT-ROY-INDUSTRIAL",
            income_type="royalty",
            rate=5.0,
            priority=10,
            conditions=[
                LegalCondition("royalty_category", "==", "industrial"),
                LegalCondition("beneficial_owner", "==", True),
            ],
        ),
        rule(
            "CZ-AT-ROY-COPYRIGHT",
            income_type="royalty",
            rate=0.0,
            priority=10,
            conditions=[
                LegalCondition("royalty_category", "==", "copyright"),
                LegalCondition("beneficial_owner", "==", True),
            ],
        ),
    ]

    industrial = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "royalty_category": "industrial",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )
    copyright_result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "royalty_category": "copyright",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert industrial.rate == 5.0
    assert industrial.selected_rule_id == "CZ-AT-ROY-INDUSTRIAL"
    assert copyright_result.rate == 0.0
    assert copyright_result.selected_rule_id == "CZ-AT-ROY-COPYRIGHT"


def test_protocol_override_replaces_base_rate_when_condition_is_met():
    rules = [
        rule(
            "CZ-CH-ROY-BASE",
            income_type="royalty",
            rate=10.0,
            priority=100,
            conditions=[LegalCondition("beneficial_owner", "==", True)],
        ),
        rule(
            "CZ-CH-ROY-PROTOCOL",
            income_type="royalty",
            rate=5.0,
            priority=10,
            effective_from=date(1996, 1, 1),
            overrides_rule_id="CZ-CH-ROY-BASE",
            conditions=[
                LegalCondition("beneficial_owner", "==", True),
                LegalCondition(
                    "recipient_country_imposes_royalty_wht_on_nonresidents",
                    "==",
                    False,
                ),
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
            "recipient_country_imposes_royalty_wht_on_nonresidents": False,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.rate == 5.0
    assert result.selected_rule_id == "CZ-CH-ROY-PROTOCOL"
    assert result.overridden_rule_id == "CZ-CH-ROY-BASE"


def test_missing_protocol_condition_does_not_silently_use_base_rate():
    rules = [
        rule(
            "CZ-CH-ROY-BASE",
            income_type="royalty",
            rate=10.0,
            priority=100,
            conditions=[LegalCondition("beneficial_owner", "==", True)],
        ),
        rule(
            "CZ-CH-ROY-PROTOCOL",
            income_type="royalty",
            rate=5.0,
            priority=10,
            effective_from=date(1996, 1, 1),
            overrides_rule_id="CZ-CH-ROY-BASE",
            conditions=[
                LegalCondition("beneficial_owner", "==", True),
                LegalCondition(
                    "recipient_country_imposes_royalty_wht_on_nonresidents",
                    "==",
                    False,
                ),
            ],
        ),
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
    assert result.missing_facts == [
        "recipient_country_imposes_royalty_wht_on_nonresidents"
    ]


def test_missing_transaction_scope_requires_review():
    rules = [
        rule(
            "CZ-CH-INT-BASE",
            income_type="interest",
            rate=0.0,
            conditions=[LegalCondition("beneficial_owner", "==", True)],
        )
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "interest",
            "source_country": "CZ",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
    assert result.missing_facts == ["recipient_country"]


def test_unverified_rule_is_not_used_for_final_rate():
    unverified_rule = LegalRule(
        rule_id="CZ-CH-INT-DRAFT",
        income_type="interest",
        source_country="CZ",
        recipient_country="CH",
        legal_instrument="treaty",
        article=11,
        paragraph="2",
        rate=5.0,
        conditions=[LegalCondition("beneficial_owner", "==", True)],
        verification_status="needs_review",
    )

    result = evaluate_legal_rules(
        [unverified_rule],
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
    assert result.selected_rule_id is None


def test_unsupported_operator_fails_closed_instead_of_crashing():
    rules = [
        rule(
            "CZ-CH-INT-UNKNOWN-OPERATOR",
            income_type="interest",
            rate=0.0,
            conditions=[LegalCondition("beneficial_owner", "contains", True)],
        )
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "interest",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None


def test_protocol_override_must_reference_existing_base_rule():
    rules = [
        rule(
            "CZ-CH-ROY-PROTOCOL",
            income_type="royalty",
            rate=5.0,
            priority=10,
            overrides_rule_id="CZ-CH-ROY-MISSING",
            conditions=[LegalCondition("beneficial_owner", "==", True)],
        )
    ]

    result = evaluate_legal_rules(
        rules,
        {
            "income_type": "royalty",
            "source_country": "CZ",
            "recipient_country": "CH",
            "beneficial_owner": True,
        },
        as_of=date(2026, 8, 3),
    )

    assert result.eligible is False
    assert result.requires_review is True
    assert result.rate is None
