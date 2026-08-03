import json
from pathlib import Path


def test_germany_uses_complete_verified_base_treaty():
    path = Path(__file__).parents[1] / "data/parsed/nemecko.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["country"] == "Německo"
    assert data["source_title"] == "18/1984 Sb."
    assert data["identity_validation"]["status"] == "validated"
    assert data["source_resolution"]["status"] == "resolved"
    assert data["source_resolution"]["method"] == "verified_mirror_html"

    articles = data["articles"]
    assert [article["number"] for article in articles] == list(range(1, 31))
    assert {
        article["number"]: article["title"]
        for article in articles
        if article["number"] in {10, 11, 12}
    } == {
        10: "Dividendy",
        11: "Úroky",
        12: "Licenční poplatky",
    }
