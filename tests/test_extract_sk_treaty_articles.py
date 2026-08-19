from __future__ import annotations

from taxtreat.tools.extract_sk_treaty_articles import (
    _article_blocks,
    _static_source_url,
    _title_matches,
    parse_treaty,
)


def _relationship():
    return {
        "recipient_country": "AT",
        "recipient_country_name": "Rakúsko",
        "treaty_publication": "48/1979",
        "official_primary_text_url": (
            "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/1979/48/"
        ),
    }


def _scopes():
    return [
        {
            "packet_id": "SK-AT-dividend-TREATY-SOURCE",
            "recipient_country": "AT",
            "income_type": "dividend",
        },
        {
            "packet_id": "SK-AT-interest-TREATY-SOURCE",
            "recipient_country": "AT",
            "income_type": "interest",
        },
        {
            "packet_id": "SK-AT-royalty-TREATY-SOURCE",
            "recipient_country": "AT",
            "income_type": "royalty",
        },
    ]


def test_static_source_url_is_deterministic():
    assert _static_source_url(
        "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/1979/48/"
    ).endswith("/1979/48/vyhlasene_znenie.html")


def test_article_blocks_support_slovak_and_czech_heading_forms():
    text = (
        "Úvod Článok 10 Dividendy text A "
        "Článek 11 Úroky text B "
        "Článok 12 Licenčné poplatky text C "
        "Článok 13 Zisky zo scudzenia text D"
    )
    blocks = _article_blocks(text)
    assert blocks["10"].startswith("Článok 10 Dividendy")
    assert blocks["11"].startswith("Článek 11 Úroky")
    assert blocks["12"].startswith("Článok 12 Licenčné poplatky")
    assert "Článok 13" not in blocks["12"]


def test_income_title_validation_is_fail_closed():
    assert _title_matches("dividend", "Článok 10 Dividendy text") is True
    assert _title_matches("interest", "Článok 11 Úroky text") is True
    assert _title_matches("royalty", "Článok 12 Licenčné poplatky text") is True
    assert _title_matches("royalty", "Článok 12 Iné príjmy text") is False


def test_parse_treaty_preserves_full_article_text_and_hash():
    html = """
    <html><body>
      <h2>Článok 10</h2><h3>Dividendy</h3>
      <p>(1) Dividendy sa môžu zdaniť v druhom štáte.</p>
      <p>(2) Daň však nepresiahne 10 % hrubej sumy.</p>
      <h2>Článok 11</h2><h3>Úroky</h3>
      <p>(1) Úroky sa môžu zdaniť iba v druhom štáte.</p>
      <h2>Článok 12</h2><h3>Licenčné poplatky</h3>
      <p>(1) Licenčné poplatky sa môžu zdaniť v druhom štáte.</p>
      <h2>Článok 13</h2><h3>Zisky zo scudzenia majetku</h3>
    </body></html>
    """
    result = parse_treaty(
        source_relationship=_relationship(),
        source_scopes=_scopes(),
        html=html,
    )

    assert len(result["scopes"]) == 3
    by_income = {row["income_type"]: row for row in result["scopes"]}

    assert by_income["dividend"]["machine_extraction_status"] == "article_extracted"
    assert "10 %" in by_income["dividend"]["article_text"]
    assert by_income["dividend"]["article_text_sha256"]

    assert by_income["interest"]["machine_extraction_status"] == "article_extracted"
    assert by_income["royalty"]["machine_extraction_status"] == "article_extracted"

    assert all(row["review_ready"] is False for row in result["scopes"])
    assert all(row["approval_eligible"] is False for row in result["scopes"])
    assert all(row["runtime_status"] == "not_released" for row in result["scopes"])


def test_missing_expected_article_is_not_silently_accepted():
    html = """
    <html><body>
      <h2>Článok 10</h2><h3>Dividendy</h3><p>text</p>
      <h2>Článok 11</h2><h3>Úroky</h3><p>text</p>
      <h2>Článok 13</h2><h3>Iné príjmy</h3><p>text</p>
    </body></html>
    """
    result = parse_treaty(
        source_relationship=_relationship(),
        source_scopes=_scopes(),
        html=html,
    )
    royalty = next(row for row in result["scopes"] if row["income_type"] == "royalty")
    assert royalty["machine_extraction_status"] == "expected_article_heading_not_found"
    assert royalty["review_ready"] is False
