import pytest

from taxtreat.parser.article_parser import parse_articles, split_paragraphs
from taxtreat.parser.detector import find_start, extract_treaty
from taxtreat.parser.normalize import repair, normalize_page
from taxtreat.parser.text_cleanup import clean_text


def test_split_paragraphs():
    text = """1. First paragraph

2. Second paragraph

3. Third paragraph"""
    paragraphs = split_paragraphs(text)
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("1.")
    assert paragraphs[2].startswith("3.")


def test_parse_articles():
    treaty = """
Article 10
Dividends
1. Dividends paragraph.

Article 11
Interest
1. Interest paragraph.
"""

    articles = parse_articles(treaty)

    assert len(articles) == 2
    assert articles[0].number == 10
    assert articles[0].title == "Dividends"
    assert "Dividends paragraph" in articles[0].text
    assert articles[1].number == 11


def test_parse_articles_without_article():
    with pytest.raises(RuntimeError):
        parse_articles("Nothing here")


def test_find_start():
    pages = [
        "random",
        "SMLOUVA\nČlánek 1",
        "Článek 2",
    ]
    assert find_start(pages) == 1


def test_extract_treaty():
    pages = [
        "cover",
        "SMLOUVA\nČlánek 1",
        "Článek 2",
    ]

    treaty, page = extract_treaty(pages)

    assert page == 2
    assert treaty.startswith("SMLOUVA")


def test_repair():
    assert repair("CÏlaÂnek") == "Článek"


def test_normalize_page():
    page = """
Strana 1

Částka

Článek 1
"""

    normalized = normalize_page(page)

    assert "Strana" not in normalized
    assert "Částka" not in normalized
    assert "Článek" in normalized


def test_clean_text():
    text = "Divi-\ndends"

    cleaned = clean_text(text)

    assert "Dividends" in cleaned

from taxtreat.parser.models import ParsedTreaty, TreatyArticle
from taxtreat.parser.normalize import normalize_pages
from taxtreat.rules.dividends import extract_dividend_rule
from taxtreat.engine.registry import build_default_registry


def test_find_start_not_found():
    import pytest

    with pytest.raises(RuntimeError):
        find_start(["cover", "random page"])


def test_treaty_article_to_dict():
    article = TreatyArticle(
        number=10,
        title="Dividends",
        text="Body",
        paragraphs=["1. Test"],
    )

    d = article.to_dict()

    assert d["number"] == 10
    assert d["title"] == "Dividends"


def test_parsed_treaty_to_dict():
    treaty = ParsedTreaty(
        country="CZ",
        source_title="Treaty",
        source_path="file.pdf",
        start_page=1,
    )

    assert treaty.to_dict()["country"] == "CZ"


def test_normalize_pages():
    result = normalize_pages(
        [
            "Strana 1\n\nČlánek 1",
            "Strana 2\n\nČlánek 2",
        ]
    )

    assert result == ["Článek 1", "Článek 2"]


def test_extract_dividend_rule():
    result = extract_dividend_rule(
        "The tax shall not exceed 5% where the beneficial owner "
        "holds 20% of the capital for at least 365 days."
    )

    assert result["transaction_type"] == "dividend"
    assert result["withholding_rates"] == [5.0]
    assert result["ownership_thresholds"] == [20.0]
    assert result["holding_period"] is not None
    assert result["beneficial_owner_required"] is True


def test_registry_has_default_dividend():
    registry = build_default_registry()

    assert registry.has("dividend")
    assert registry.get("dividend") is not None
    assert registry.get("interest") is None


def test_split_paragraphs_empty_text():
    assert split_paragraphs("") == []
    assert split_paragraphs("   ") == []


def test_repair_spaced_article_heading():
    assert repair("CÏ l aÂ ne k 1 0") == "Článek 10"
    assert repair("CÏ laÂ n e k 1 2") == "Článek 12"
