import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "app" / "web" / "treaty-excerpt-locales"


def _load(country: str) -> dict:
    return json.loads((COUNTRY_DIR / f"{country}.json").read_text(encoding="utf-8"))


def test_ph_interest_exemption_has_explicit_rule_specific_english_excerpt():
    payload = _load("PH")
    entry = payload["rules"]["CZ-PH-INTEREST-CURRENT-2"]
    assert entry["article"] == "11"
    assert entry["en"]["authority"] == "Bureau of Internal Revenue, Philippines"
    assert "shall be exempted from tax" in entry["en"]["text"]


def test_singapore_articles_and_royalty_branches_use_official_iras_source():
    payload = _load("SG")
    assert payload["recipient_country"] == "SG"
    for article in ("10", "11", "12"):
        locale = payload["articles"][article]["en"]
        assert locale["authority"] == "Inland Revenue Authority of Singapore"
        assert locale["status"] == "official_synthesised_text"
        assert locale["source_url"].startswith("https://www.iras.gov.sg/")
    assert "5 per cent" in payload["rules"]["CZ-SG-ROYALTY-CURRENT-2"]["en"]["text"]
    assert "10 per cent" in payload["rules"]["CZ-SG-ROYALTY-CURRENT-3"]["en"]["text"]
    assert "only for royalties other than" in payload["rules"]["CZ-SG-ROYALTY-CURRENT-1"]["en"]["text"]


def test_japan_articles_use_official_mof_synthesised_text():
    payload = _load("JP")
    assert payload["recipient_country"] == "JP"
    for article in ("10", "11", "12"):
        locale = payload["articles"][article]["en"]
        assert locale["authority"] == "Ministry of Finance, Japan"
        assert locale["status"] == "official_synthesised_text"
        assert locale["source_url"].startswith("https://www.mof.go.jp/")
    assert "10 per cent" in payload["articles"]["10"]["en"]["text"]
    assert "15 per cent" in payload["articles"]["10"]["en"]["text"]
    assert "shall be exempt from tax" in payload["articles"]["11"]["en"]["text"]
    assert "Cultural royalties shall be exempt" in payload["articles"]["12"]["en"]["text"]
