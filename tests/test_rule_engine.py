from taxtreat.services.rule_engine import RuleEngine, build_dividend_rule


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
