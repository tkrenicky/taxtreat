from pathlib import Path

from taxtreat.parsers.dtt_parser import parse_articles


def test_parse_articles():
    text = Path("tests/data/dtt/sample_dtt.txt").read_text()

    articles = parse_articles(text)

    assert len(articles) == 3

    assert articles[0].article == 10
    assert articles[0].rates == [5, 15]

    assert articles[1].article == 11
    assert articles[1].rates == []

    assert articles[2].article == 12
    assert articles[2].rates == [5]
