import json

from taxtreat.engine.rule_extractor import extract_dividend_rules


def test_extract_austria_dividend_rules():
    data = json.load(open("data/parsed/austria.json", encoding="utf-8"))

    article10 = next(
        article
        for article in data["articles"]
        if article["number"] == 10
    )

    rules = extract_dividend_rules(article10["text"])

    assert rules["rates"] == [10]
    assert rules["minimum_ownership_percent"] == 10
    assert rules["beneficial_owner_required"] is True
