from taxtreat.engine.models import Rule
from taxtreat.services.analyzer import (
    TreatyAnalyzer,
    interest_rule,
    royalties_rule,
)


class FakeRepository:
    def get_full_article_text(self, article_number):
        return f"Article {article_number}"


def test_interest_rule():
    rule = interest_rule("dummy")

    assert rule.article == 11
    assert rule.transaction_type == "interest"


def test_royalties_rule():
    rule = royalties_rule("dummy")

    assert rule.article == 12
    assert rule.transaction_type == "royalties"


def test_analyze_dividends(monkeypatch):
    def fake_dividend_rule(text):
        assert text == "Article 10"
        return Rule(article=10, transaction_type="dividend")

    monkeypatch.setattr(
        "taxtreat.services.analyzer.dividend_rule",
        fake_dividend_rule,
    )

    analyzer = TreatyAnalyzer(FakeRepository())

    rule = analyzer.analyze_dividends()

    assert rule.article == 10
    assert rule.transaction_type == "dividend"


def test_analyze_interest():
    analyzer = TreatyAnalyzer(FakeRepository())

    rule = analyzer.analyze_interest()

    assert rule.article == 11
    assert rule.transaction_type == "interest"


def test_analyze_royalties():
    analyzer = TreatyAnalyzer(FakeRepository())

    rule = analyzer.analyze_royalties()

    assert rule.article == 12
    assert rule.transaction_type == "royalties"
