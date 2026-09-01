from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _sk_english_report_payload():
    return {
        "source_country": "SK",
        "recipient_country": "AT",
        "income_type": "dividend",
        "transaction_date": "2026-08-19",
        "facts": {
            "__report_language": "en",
            "recipient_entity_type": "corporate",
            "distribution_category_is_section_3_1_f": False,
            "distribution_is_tax_deductible_for_payer": False,
        },
        "determinations": {},
    }


def test_released_sk_runtime_generates_source_specific_english_report_end_to_end():
    response = client.post("/analysis/report", json=_sk_english_report_payload())

    assert response.status_code == 200
    payload = response.json()
    report = payload["report"]
    html = payload["html"]

    assert report["language"] == "en"
    assert report["scope"]["source_country"] == "SK"
    assert report["scope"]["recipient_country"] == "AT"
    assert report["result"]["status"] == "REVIEW_REQUIRED"

    legal_sources = [
        source
        for source in report["official_sources"]
        if source.get("legal_layer") in {"treaty", "protocol", "mli"}
    ]
    assert legal_sources
    for source in legal_sources:
        assert source["excerpt"]
        assert source["excerpt_language"] == "en"
        assert source["excerpt_status"] in {
            "verified_structured_rule_summary",
            "review_required_structured_rule_summary",
        }
        assert "not treaty wording" in source["excerpt_status_label"].lower()
        assert "Slovak source-country legal data" in source["excerpt"]
        assert "Czech source-state" not in source["excerpt"]
        assert "CZ-AT" not in source["excerpt"]
        assert "slov-lex.sk" in str(source.get("source_url") or "")

    assert '<html lang="en">' in html
    assert "Slovak withholding tax information" in html
    assert "Czech withholding tax information" not in html
    assert "Czech withholding tax" not in html
    assert "Czech Income Taxes Act" not in html
    assert "586/1992" not in html
    assert "§ 38da" not in html
    assert "Informace k české srážkové dani" not in html
    assert "Česká srážková daň" not in html
    assert "Informácie k slovenskej zrážkovej dani" not in html
