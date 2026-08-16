from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_canonical_treaty_texts.py"


def _module():
    spec = importlib.util.spec_from_file_location("canonical_treaty_texts", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload(kind: str, heading: str):
    return {
        "fragmenty": [
            {"fragmentId": 1, "hloubka": 3, "typ": kind, "xhtml": heading},
            {"fragmentId": 2, "hloubka": 4, "typ": "Nadpis", "xhtml": "DIVIDENDY"},
            {"fragmentId": 3, "hloubka": 4, "typ": "Odstavec", "xhtml": "1. První odstavec."},
            {"fragmentId": 4, "hloubka": 3, "typ": kind, "xhtml": "Článek 11"},
            {"fragmentId": 5, "hloubka": 4, "typ": "Odstavec", "xhtml": "Text dalšího článku."},
        ]
    }


def test_extracts_standard_czech_article_and_stops_at_next_article():
    module = _module()
    text, fragment_ids = module.extract_article(_payload("Clanek", "Článek 10"), 10)
    assert text == "Článek 10\nDIVIDENDY\n1. První odstavec."
    assert fragment_ids == [1, 2, 3]


def test_extracts_international_treaty_uppercase_article_heading():
    module = _module()
    result = module.extract_article(_payload("ClanekMS", "<var>ČLÁNEK 10</var>"), 10)
    assert result is not None
    text, _ = result
    assert text.startswith("ČLÁNEK 10\nDIVIDENDY")


def test_extracts_abbreviated_czech_article_heading():
    module = _module()
    result = module.extract_article(_payload("Clanek", "Čl. 10"), 10)
    assert result is not None
    text, _ = result
    assert text.startswith("Čl. 10\nDIVIDENDY")
