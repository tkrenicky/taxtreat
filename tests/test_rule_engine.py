from taxtreat.services.rule_engine import (
    RuleEngine,
    build_dividend_rule,
    build_interest_rule,
    build_royalty_rule,
)


class FakeRepository:
    def get_full_article_text(self, article_number):
        assert article_number == 10
        return "ARTICLE TEXT"


def test_extract_dividend_rule(monkeypatch):
    called = {}

    def fake_dividend_rule(text):
        called["text"] = text
        return {"rate": "5%"}

    monkeypatch.setattr(
        "taxtreat.services.rule_engine.dividend_rule",
        fake_dividend_rule,
    )

    engine = RuleEngine(FakeRepository())

    result = engine.extract_dividend_rule()

    assert result == {"rate": "5%"}
    assert called["text"] == "ARTICLE TEXT"


def test_build_dividend_rule(monkeypatch):
    class FakeRepository:
        def __init__(self, db_path):
            self.db_path = db_path

        def get_full_article_text(self, article_number):
            assert article_number == 10
            return "DB ARTICLE"

    def fake_dividend_rule(text):
        return {"text": text}

    monkeypatch.setattr(
        "taxtreat.services.rule_engine.TreatyRepository",
        FakeRepository,
    )

    monkeypatch.setattr(
        "taxtreat.services.rule_engine.dividend_rule",
        fake_dividend_rule,
    )

    result = build_dividend_rule(10, "dummy.db")

    assert result == {"text": "DB ARTICLE"}



class IncomeRepository:
    def get_full_article_text(self, article_number):
        return f"ARTICLE {article_number}"


def test_extract_interest_rule(monkeypatch):
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.interest_rule",
        lambda text: {"type": "interest", "text": text},
    )

    result = RuleEngine(IncomeRepository()).extract_interest_rule()

    assert result == {"type": "interest", "text": "ARTICLE 11"}


def test_extract_royalty_rule(monkeypatch):
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.royalty_rule",
        lambda text: {"type": "royalty", "text": text},
    )

    result = RuleEngine(IncomeRepository()).extract_royalty_rule()

    assert result == {"type": "royalty", "text": "ARTICLE 12"}


def test_build_interest_rule(monkeypatch):
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.TreatyRepository",
        lambda db_path: IncomeRepository(),
    )
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.interest_rule",
        lambda text: {"text": text},
    )

    assert build_interest_rule(11, "dummy.db") == {"text": "ARTICLE 11"}


def test_build_royalty_rule(monkeypatch):
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.TreatyRepository",
        lambda db_path: IncomeRepository(),
    )
    monkeypatch.setattr(
        "taxtreat.services.rule_engine.royalty_rule",
        lambda text: {"text": text},
    )

    assert build_royalty_rule(12, "dummy.db") == {"text": "ARTICLE 12"}
