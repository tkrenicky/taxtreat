from __future__ import annotations

from taxtreat.tools.run_sk_machine_ingestion import _resolve_treaty_source


def test_standard_slov_lex_treaty_uses_static_html():
    source = {
        "recipient_country": "AT",
        "official_primary_text_url": (
            "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/1979/48/"
        ),
    }

    url, content_type = _resolve_treaty_source(source)

    assert url.endswith("/1979/48/vyhlasene_znenie.html")
    assert content_type == "html"


def test_oman_uses_official_slov_lex_pdf_override():
    source = {
        "recipient_country": "OM",
        "official_primary_text_url": (
            "https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2021/548/"
        ),
    }

    url, content_type = _resolve_treaty_source(source)

    assert "/pdf/prilohy/SK/ZZ/2021/548/" in url
    assert url.endswith(".pdf")
    assert content_type == "pdf"


def test_taiwan_uses_official_mf_financial_bulletin_pdf():
    source = {
        "recipient_country": "TW",
        "official_primary_text_url": (
            "https://www.mfsr.sk/files/archiv/financny-spravodajca/"
            "3497/63/FS_09_2011.pdf"
        ),
    }

    url, content_type = _resolve_treaty_source(source)

    assert url.endswith("FS_09_2011.pdf")
    assert "mfsr.sk" in url
    assert content_type == "pdf"


def test_unknown_source_remains_fail_closed():
    source = {
        "recipient_country": "XX",
        "official_primary_text_url": None,
    }

    assert _resolve_treaty_source(source) == (None, "unknown")
