import json
from pathlib import Path


def load_rules():
    path = Path("data/extracted/austria.json")
    return json.loads(path.read_text(encoding="utf-8"))["income_rules"]


def test_austrian_dividend_rules():
    rule = load_rules()["dividends"]

    assert rule["article"] == 10
    assert rule["standard_rate"] == 10
    assert rule["reduced_rates"][0]["rate"] == 0
    assert (
        rule["reduced_rates"][0]["conditions"]["minimum_ownership_percent"]
        == 10
    )


def test_austrian_interest_rule():
    rule = load_rules()["interest"]

    assert rule["article"] == 11
    assert rule["standard_rate"] == 0


def test_austrian_royalty_categories():
    rule = load_rules()["royalties"]

    rates = {
        item["conditions"]["royalty_category"]: item["rate"]
        for item in rule["rates"]
    }

    assert rates == {
        "Article 12(3)(a)": 5,
        "Article 12(3)(b)": 0,
    }
