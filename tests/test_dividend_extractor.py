from taxtreat.engine.extractors import dividend_rule
from taxtreat.engine.models import ConditionType


def _condition(rule, rate, condition_type):
    selected = next(item for item in rule.rates if item.rate == rate)
    return next(
        condition
        for condition in selected.conditions
        if condition.condition_type == condition_type
    )


def test_english_two_rate_article_links_ownership_only_to_reduced_rate():
    text = """
    However, if the beneficial owner is a resident of the other State,
    the tax so charged shall not exceed:
    a) 5 per cent of the gross amount if the beneficial owner is a company
       which holds directly at least 25 per cent of the capital;
    b) 15 per cent of the gross amount in all other cases.
    """
    rule = dividend_rule(text)

    assert [rate.rate for rate in rule.rates] == [5.0, 15.0]
    assert _condition(rule, 5.0, ConditionType.minimum_ownership).value == "25"

    fallback = next(rate for rate in rule.rates if rate.rate == 15.0)
    assert not any(
        condition.condition_type == ConditionType.minimum_ownership
        for condition in fallback.conditions
    )


def test_czech_two_rate_article_does_not_treat_ownership_as_tax_rate():
    text = """
    Jestliže je skutečný vlastník dividend rezidentem druhého smluvního státu,
    daň takto uložená nepřesáhne:
    a) 5 % hrubé částky dividend, jestliže skutečný vlastník je společnost,
       která přímo vlastní nejméně 25 % základního kapitálu;
    b) 15 % hrubé částky dividend ve všech ostatních případech.
    """
    rule = dividend_rule(text)

    assert [rate.rate for rate in rule.rates] == [5.0, 15.0]
    assert 25.0 not in [rate.rate for rate in rule.rates]
    assert _condition(rule, 5.0, ConditionType.minimum_ownership).value == "25"


def test_holding_period_is_attached_only_to_relevant_rate():
    text = """
    The tax so charged shall not exceed:
    a) 0 per cent where the beneficial owner is a company that holds directly
       at least 10 per cent of the capital for an uninterrupted period of at
       least 365 days;
    b) 15 per cent in all other cases.
    """
    rule = dividend_rule(text)

    holding = _condition(rule, 0.0, ConditionType.minimum_holding_period)
    assert holding.value == "365"
    assert holding.unit == "days"

    fallback = next(rate for rate in rule.rates if rate.rate == 15.0)
    assert not any(
        condition.condition_type == ConditionType.minimum_holding_period
        for condition in fallback.conditions
    )


def test_inline_lettered_clauses_are_extracted_separately():
    text = (
        "If the beneficial owner is resident in the other State, the tax "
        "shall not exceed: a) 5 per cent where the beneficial owner is a "
        "company holding directly at least 20 per cent of the capital; "
        "b) 15 per cent in all other cases."
    )

    rule = dividend_rule(text)

    assert [rate.rate for rate in rule.rates] == [5.0, 15.0]
    assert _condition(
        rule,
        5.0,
        ConditionType.minimum_ownership,
    ).value == "20"

    fallback = next(rate for rate in rule.rates if rate.rate == 15.0)
    assert not any(
        condition.condition_type == ConditionType.minimum_ownership
        for condition in fallback.conditions
    )


def test_inline_numbered_clauses_are_extracted_separately():
    text = (
        "The tax shall not exceed: (1) 0 per cent if the beneficial owner "
        "holds at least 10 per cent of the voting power; "
        "(2) 15 per cent in all other cases."
    )

    rule = dividend_rule(text)

    assert [rate.rate for rate in rule.rates] == [0.0, 15.0]
    assert _condition(
        rule,
        0.0,
        ConditionType.minimum_ownership,
    ).value == "10"


def test_single_rate_and_empty_text():
    single = dividend_rule(
        "If the beneficial owner is resident in the other State, "
        "the tax so charged shall not exceed 10 per cent of the gross amount."
    )
    empty = dividend_rule("")

    assert [rate.rate for rate in single.rates] == [10.0]
    assert single.extraction_status == "confirmed"
    assert empty.rates == []
    assert empty.extraction_status == "incomplete"


def test_extractor_remaining_edge_cases():
    from taxtreat.engine.extractors import (
        _normalise_unit,
        extract_conditions,
        dividend_rule,
    )

    assert _normalise_unit("month") == "months"
    assert _normalise_unit("měsíců") == "months"
    assert _normalise_unit("year") == "years"
    assert _normalise_unit("roků") == "years"

    assert extract_conditions("") == []

    rule = dividend_rule("This article contains no withholding tax percentage.")

    assert rule.rate is None
    assert rule.rates == []
    assert rule.extraction_status == "incomplete"


def test_austrian_exemption_without_explicit_zero_percentage():
    from taxtreat.engine.models import ConditionType
    from taxtreat.engine.extractors import dividend_rule

    text = """
    a) Jestlize skutecný vlastnõk dividend je rezidentem druhého státu,
    dan nepresáhne 10 procent hrubé cástky dividend.

    b) Jestlize skutecný vlastnõk je spolecnost, která vlastnõ nejméne
    10 procent kapitálu spolecnosti vyplácejõcõ dividendy, tyto dividendy
    podléhajõ zdanenõ jen ve smluvnõm státe skutecného vlastnõka.
    """

    rule = dividend_rule(text)

    assert {rate.rate for rate in rule.rates} == {0.0, 10.0}

    zero_rate = next(rate for rate in rule.rates if rate.rate == 0.0)

    assert any(
        condition.condition_type == ConditionType.minimum_ownership
        and condition.value == "10"
        for condition in zero_rate.conditions
    )
    assert any(
        condition.condition_type == ConditionType.beneficial_owner
        for condition in zero_rate.conditions
    )
