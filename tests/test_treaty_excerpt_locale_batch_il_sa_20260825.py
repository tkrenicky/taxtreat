import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "app/web/treaty-excerpt-locales"


def test_il_sa_articles_10_11_12_use_official_english_sources():
    expectations = {
        "IL": ("Israel Tax Authority / Government of Israel", "official_synthesised_text"),
        "SA": ("Zakat, Tax and Customs Authority, Saudi Arabia", "official_treaty_text"),
    }
    for country, (authority, status) in expectations.items():
        payload = json.loads((COUNTRY_DIR / f"{country}.json").read_text(encoding="utf-8"))
        assert payload["source_country"] == "CZ"
        assert payload["recipient_country"] == country
        for article in ("10", "11", "12"):
            locale = payload["articles"][article]["en"]
            assert locale["language"] == "en"
            assert locale["status"] == status
            assert locale["authority"] == authority
            assert locale["source_url"].startswith("https://")
            assert locale["text"].startswith(f"Article {article}")


def test_il_decisive_rates_and_interest_exemption_are_present():
    payload = json.loads((COUNTRY_DIR / "IL.json").read_text(encoding="utf-8"))
    assert "5 per cent" in payload["articles"]["10"]["en"]["text"]
    assert "15 per cent" in payload["articles"]["10"]["en"]["text"]
    assert "10 per cent" in payload["articles"]["11"]["en"]["text"]
    assert "shall be taxable only in that other State" in payload["articles"]["11"]["en"]["text"]
    assert "5 per cent" in payload["articles"]["12"]["en"]["text"]


def test_sa_decisive_treaty_outcomes_are_present():
    payload = json.loads((COUNTRY_DIR / "SA.json").read_text(encoding="utf-8"))
    assert "5 per cent" in payload["articles"]["10"]["en"]["text"]
    assert "shall be taxable only in that other State" in payload["articles"]["11"]["en"]["text"]
    assert "10 per cent" in payload["articles"]["12"]["en"]["text"]
