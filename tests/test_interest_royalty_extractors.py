from taxtreat.engine.decision_engine import evaluate
from taxtreat.engine.extractors import interest_rule, royalty_rule
from taxtreat.engine.models import ConditionType
from taxtreat.engine.registry import build_default_registry


def condition_types(rule):
    return {
        condition.condition_type
        for rate in rule.rates
        for condition in rate.conditions
    }


def test_interest_rule_extracts_ten_percent_rate():
    text = """
    1. Interest arising in one Contracting State and paid to a resident
    of the other Contracting State may be taxed in that other State.
    2. However, if the beneficial owner of the interest is a resident
    of the other State, the tax shall not exceed 10 percent of the
    gross amount of the interest.
    """

    rule = interest_rule(text)

    assert rule.article == 11
    assert rule.transaction_type == "interest"
    assert rule.extraction_status == "confirmed"
    assert [rate.rate for rate in rule.rates] == [10.0]
    assert ConditionType.beneficial_owner in condition_types(rule)

    result = evaluate(rule, {"beneficial_owner": True})
    assert result.eligible is True
    assert result.withholding_rate == 10.0


def test_interest_rule_extracts_source_state_exemption():
    text = """
    Interest arising in one Contracting State and beneficially owned
    by a resident of the other Contracting State shall be taxable only
    in that other State.
    """

    rule = interest_rule(text)

    assert rule.extraction_status == "confirmed"
    assert [rate.rate for rate in rule.rates] == [0.0]
    assert rule.rates[0].legal_basis == "Article 11"


def test_royalty_rule_extracts_five_percent_rate():
    text = """
    Royalties arising in one Contracting State may also be taxed in
    that State, but if the beneficial owner is a resident of the other
    Contracting State, the tax shall not exceed 5 percent of the gross
    amount of the royalties.
    """

    rule = royalty_rule(text)

    assert rule.article == 12
    assert rule.transaction_type == "royalty"
    assert rule.extraction_status == "confirmed"
    assert [rate.rate for rate in rule.rates] == [5.0]
    assert ConditionType.beneficial_owner in condition_types(rule)

    result = evaluate(rule, {"beneficial_owner": True})
    assert result.eligible is True
    assert result.withholding_rate == 5.0


def test_royalty_rule_extracts_source_state_exemption():
    text = """
    Royalties arising in one Contracting State and beneficially owned
    by a resident of the other Contracting State shall be taxable only
    in that other State.
    """

    rule = royalty_rule(text)

    assert rule.extraction_status == "confirmed"
    assert [rate.rate for rate in rule.rates] == [0.0]
    assert rule.rates[0].legal_basis == "Article 12"


def test_interest_and_royalty_empty_text_are_incomplete():
    interest = interest_rule("")
    royalty = royalty_rule("")

    assert interest.extraction_status == "incomplete"
    assert interest.rates == []
    assert royalty.extraction_status == "incomplete"
    assert royalty.rates == []


def test_default_registry_contains_interest_and_royalty_extractors():
    registry = build_default_registry()

    assert registry.get("interest") is interest_rule
    assert registry.get("royalty") is royalty_rule
