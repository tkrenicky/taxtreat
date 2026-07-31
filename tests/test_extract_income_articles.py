import json
from pathlib import Path


def test_austria_contains_income_articles():
    path = Path("data/extracted/austria.json")

    assert path.exists()

    data = json.loads(path.read_text(encoding="utf-8"))

    assert set(data["articles"]) == {"10", "11", "12"}
