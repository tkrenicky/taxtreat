from pathlib import Path

from taxtreat.extractors.treaty_extractor import extract_treaty


def test_extract_treaty():
    text = Path("tests/data/dtt/sample_dtt.txt").read_text()

    treaty = extract_treaty(text)

    assert treaty[10]["rates"] == [5, 15]
    assert treaty[10]["beneficial_owner_required"] is True
    assert treaty[10]["minimum_ownership_percent"] == 10

    assert treaty[11]["rates"] == []

    assert treaty[12]["rates"] == [5]
