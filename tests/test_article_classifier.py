import pytest

from taxtreat.engine.article_classifier import classify_article


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("", "other"),
        (None, "other"),
        ("Article 10 – Dividends", "dividend"),
        ("DIVIDENDY", "dividend"),
        ("Článek 11: Úroky", "interest"),
        ("Interest", "interest"),
        ("Licenční poplatky", "royalty"),
        ("Royalties", "royalty"),
        ("Stálá provozovna", "permanent_establishment"),
        ("Permanent Establishment", "permanent_establishment"),
        ("Zisky podniků", "business_profits"),
        ("Business Profits", "business_profits"),
        ("Kapitálové zisky", "capital_gains"),
        ("Capital Gains", "capital_gains"),
        ("Zaměstnání", "employment"),
        ("Employment Income", "employment"),
        ("General Provisions", "other"),
    ],
)
def test_classify_article(title, expected):
    assert classify_article(title) == expected


def test_classifier_normalizes_punctuation_and_whitespace():
    assert classify_article("  ARTICLE 10:   DIVIDENDS!!!  ") == "dividend"


def test_classifier_uses_tolerant_income_article_matching():
    from taxtreat.engine.article_classifier import classify_article

    assert classify_article("U roky") == "interest"
    assert classify_article("PŘ IJMY Z POHLEDÁVEK") == "interest"
    assert classify_article("Licencnõ poplatky") == "royalty"
    assert classify_article("DIVIDENDS") == "dividend"


def test_classifier_uses_article_body_when_heading_is_only_number():
    assert classify_article("1.", "Úroky mající zdroj v jednom smluvním státě") == "interest"
