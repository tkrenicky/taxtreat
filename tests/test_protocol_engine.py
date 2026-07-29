from datetime import date

from taxtreat.engine.models import ConditionType, Protocol, ProtocolChange, Rule, WHTCondition, WHTRate
from taxtreat.engine.protocol_engine import ProtocolEngine


def build_base_rule() -> Rule:
    return Rule(
        article=10,
        transaction_type="dividend",
        rate=10.0,
        rates=[
            WHTRate(
                rate=10.0,
                conditions=[
                    WHTCondition(
                        condition_type=ConditionType.minimum_ownership,
                        operator=">=",
                        value="10",
                        unit="%",
                        description="minimum ownership",
                    )
                ],
                legal_basis="Original legal basis",
                priority=0,
            )
        ],
        conditions=[
            WHTCondition(
                condition_type=ConditionType.minimum_ownership,
                operator=">=",
                value="10",
                unit="%",
                description="minimum ownership",
            )
        ],
        legal_basis="Original legal basis",
    )


def test_protocol_can_replace_rate_and_legal_basis_without_mutating_rule():
    base_rule = build_base_rule()
    protocol = Protocol(
        name="Protocol 1",
        effective_date=date(2024, 1, 1),
        changes=[
            ProtocolChange(rate=5.0, legal_basis="Updated legal basis"),
        ],
    )

    engine = ProtocolEngine()
    updated_rule = engine.apply(base_rule, [protocol], effective_date=date(2024, 2, 1))

    assert updated_rule.rate == 5.0
    assert updated_rule.rates[0].rate == 5.0
    assert updated_rule.legal_basis == "Updated legal basis"
    assert updated_rule.rates[0].legal_basis == "Updated legal basis"
    assert base_rule.rate == 10.0
    assert base_rule.rates[0].rate == 10.0
    assert base_rule.legal_basis == "Original legal basis"


def test_protocol_can_add_and_remove_conditions():
    base_rule = build_base_rule()
    protocol = Protocol(
        name="Protocol 2",
        effective_date=date(2024, 1, 1),
        changes=[
            ProtocolChange(
                add_conditions=[
                    WHTCondition(
                        condition_type=ConditionType.beneficial_owner,
                        operator="==",
                        value="true",
                        description="beneficial owner required",
                    )
                ],
                remove_condition_types=[ConditionType.minimum_ownership],
            )
        ],
    )

    engine = ProtocolEngine()
    updated_rule = engine.apply(base_rule, [protocol], effective_date=date(2024, 2, 1))

    assert len(updated_rule.rates[0].conditions) == 1
    assert updated_rule.rates[0].conditions[0].condition_type == ConditionType.beneficial_owner
    assert len(updated_rule.conditions) == 1
    assert updated_rule.conditions[0].condition_type == ConditionType.beneficial_owner


def test_newest_applicable_protocol_takes_precedence():
    base_rule = build_base_rule()
    older_protocol = Protocol(
        name="Older",
        effective_date=date(2024, 1, 1),
        changes=[ProtocolChange(rate=7.0, legal_basis="Older basis")],
    )
    newer_protocol = Protocol(
        name="Newer",
        effective_date=date(2024, 6, 1),
        changes=[ProtocolChange(rate=3.0, legal_basis="Newer basis")],
    )

    engine = ProtocolEngine()
    updated_rule = engine.apply(base_rule, [older_protocol, newer_protocol], effective_date=date(2024, 7, 1))

    assert updated_rule.rate == 3.0
    assert updated_rule.legal_basis == "Newer basis"


def test_protocols_are_skipped_before_their_effective_date():
    base_rule = build_base_rule()
    protocol = Protocol(
        name="Future",
        effective_date=date(2025, 1, 1),
        changes=[ProtocolChange(rate=2.0)],
    )

    engine = ProtocolEngine()
    updated_rule = engine.apply(base_rule, [protocol], effective_date=date(2024, 12, 31))

    assert updated_rule.rate == 10.0
    assert updated_rule.rates[0].rate == 10.0


def test_protocol_is_ignored_when_it_does_not_match_rule_scope():
    base_rule = build_base_rule()
    protocol = Protocol(
        name="Article 11 only",
        effective_date=date(2024, 1, 1),
        article=11,
        transaction_type="interest",
        changes=[ProtocolChange(rate=2.0)],
    )

    engine = ProtocolEngine()
    updated_rule = engine.apply(base_rule, [protocol], effective_date=date(2024, 2, 1))

    assert updated_rule.rate == 10.0
