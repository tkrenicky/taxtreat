import pytest

from taxtreat.tools.treaty_income_semantics import article_number, classify_income, roman_to_int


@pytest.mark.parametrize(
    "token, expected",
    [("VIII", 8), ("IX", 9), ("X", 10), ("XI", 11), ("XII", 12), ("13", 13)],
)
def test_article_number_accepts_arabic_and_general_roman(token, expected):
    assert article_number(token) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Artikel VIII Dividenden (1) Dividenden, die eine Gesellschaft zahlt...", "dividend"),
        ("ARTICLE X INTEREST 1. Interest arising in a Contracting State...", "interest"),
        ("Artikel XI Lizenzgebühren (1) Lizenzgebühren, die aus einem Staat stammen...", "royalty"),
        ("ARTICLE 10 DIVIDENDS Dividends paid by a company...", "dividend"),
        ("ARTICLE 11 INTEREST Interest arising in a Contracting State...", "interest"),
        ("ARTICLE 12 ROYALTIES Royalties arising in a Contracting State...", "royalty"),
    ],
)
def test_classify_income_uses_heading_or_lead_clause(text, expected):
    assert classify_income(text) == expected


def test_classify_income_does_not_follow_late_cross_reference():
    text = (
        "ARTICLE IX DIVIDENDS Dividends paid by a company resident in one State may be taxed... "
        + "x" * 150
        + " The provisions of Article XI concerning interest shall not apply here."
    )
    assert classify_income(text) == "dividend"


def test_classify_income_fails_closed_when_multiple_income_labels_compete_immediately():
    assert classify_income("ARTICLE X DIVIDENDS AND INTEREST special mixed provision") is None


@pytest.mark.parametrize("token", ["", "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII", "ABC", "0"])
def test_article_number_rejects_invalid_values(token):
    with pytest.raises(ValueError):
        article_number(token)


def test_classify_income_rejects_invalid_scan_window():
    with pytest.raises(ValueError):
        classify_income("ARTICLE 10 DIVIDENDS", scan_chars=0)
