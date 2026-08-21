from __future__ import annotations

from pathlib import Path

import taxtreat.tools.run_sk_machine_ingestion as ingestion
from taxtreat.tools.run_sk_machine_ingestion import (
    _resolve_treaty_source,
    _taiwan_primary_summary_rows,
)


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


def test_taiwan_timeout_fallback_is_explicit_and_never_released(tmp_path, monkeypatch):
    fallback = {
        "recipient_country": "TW",
        "primary_source": {
            "url": "https://www.mfsr.sk/files/archiv/financny-spravodajca/3497/63/FS_09_2011.pdf"
        },
        "scopes": {
            "dividend": {
                "article": "10",
                "rate_candidates_percent": [10.0],
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "exclusive_residence_taxation_candidate": False,
                "holding_period_candidates": [],
            },
            "interest": {
                "article": "11",
                "rate_candidates_percent": [10.0],
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "exclusive_residence_taxation_candidate": False,
                "holding_period_candidates": [],
            },
            "royalty": {
                "article": "12",
                "rate_candidates_percent": [5.0, 10.0],
                "beneficial_owner_wording_present": True,
                "pe_or_fixed_base_carveout_wording_present": True,
                "exclusive_residence_taxation_candidate": False,
                "holding_period_candidates": [],
            },
        },
    }
    fallback_path = tmp_path / "tw_fallback.json"
    import json
    fallback_path.write_text(json.dumps(fallback), encoding="utf-8")
    monkeypatch.setattr(ingestion, "TW_FALLBACK_PATH", fallback_path)
    monkeypatch.setattr(ingestion, "ROOT", Path(tmp_path))

    source = {
        "recipient_country": "TW",
        "recipient_country_name": "Taiwan",
        "treaty_publication": "FS 9/2011 ozn. č. 31",
        "official_primary_text_url": fallback["primary_source"]["url"],
    }
    scopes = [
        {
            "packet_id": f"SK-TW-{income}-TREATY-SOURCE",
            "recipient_country": "TW",
            "income_type": income,
        }
        for income in ("dividend", "interest", "royalty")
    ]

    relationship, rows = _taiwan_primary_summary_rows(
        source,
        scopes,
        TimeoutError("timed out"),
    )

    assert relationship["machine_extraction_status"] == "completed_primary_summary_fallback"
    assert relationship["evidence_quality"] == (
        "official_primary_source_summary_fallback_not_byte_exact"
    )
    assert len(rows) == 3
    assert all(row["approval_eligible"] is False for row in rows)
    assert all(row["runtime_status"] == "not_released" for row in rows)
    assert [row["actual_article"] for row in rows] == ["10", "11", "12"]
