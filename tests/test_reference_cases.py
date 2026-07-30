from pathlib import Path
import yaml


REFERENCE_DIR = Path("reference_cases")


def load_cases():
    for file in REFERENCE_DIR.rglob("*.yaml"):
        yield yaml.safe_load(file.read_text(encoding="utf-8"))


def test_reference_cases_have_valid_structure():
    cases = list(load_cases())

    assert cases, "No reference cases found."

    for case in cases:
        assert "id" in case
        assert "payer_country" in case
        assert "recipient_country" in case
        assert "income_type" in case
        assert "facts" in case
        assert "expected" in case

        expected = case["expected"]

        assert "treaty" in expected
        assert "rate" in expected["treaty"]
        assert "article" in expected["treaty"]

        assert isinstance(expected["treaty"]["rate"], (int, float))
