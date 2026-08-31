from fastapi.testclient import TestClient

from app.main import app
from taxtreat.services.legal_sources import load_verified_provisions
from taxtreat.services.reporting.client_report import _cz_ir_domestic_exemption_html


def _ad_dividend_payload():
    return {
        "source_country": "CZ",
        "recipient_country": "AD",
        "income_type": "dividend",
        "transaction_date": "2026-08-16",
        "facts": {
            "recipient_tax_residence": "confirmed",
            "recipient_legal_form": "company",
            "beneficial_owner": True,
            "beneficial_owner_confirmed": True,
            "anti_abuse_review_passed": True,
            "residence_certificate_available": True,
            "no_pe_connection": True,
            "pe_connection": False,
            "ownership_percent": 100,
            "direct_ownership": True,
            "holding_period_months": 24,
            "recipient_is_qualifying_company": True,
        },
        "determinations": {},
    }


def test_analysis_report_uses_canonical_treaty_text_not_stage6_excerpt():
    client = TestClient(app)
    response = client.post("/analysis/report", json=_ad_dividend_payload())

    assert response.status_code == 200
    payload = response.json()
    report = payload["report"]
    html = payload["html"]
    treaty_sources = [
        source
        for source in report["official_sources"]
        if source["legal_layer"] == "treaty"
    ]
    assert treaty_sources

    canonical = load_verified_provisions()["CZ-AD|treaty|10"]
    source = treaty_sources[0]
    assert source["excerpt"] == canonical["text"]
    assert source["excerpt_sha256"] == canonical["verified_text_sha256"]
    assert source["source_url"] == canonical["source_url"]
    assert canonical["text"] in html

    # Known damaged Stage 6 spellings must never leak into the report once the
    # canonical e-Sbírka text has been attached.
    assert "rozdili zisk" not in source["excerpt"]
    assert "vyplacejici" not in source["excerpt"]
    assert "rozdili zisk" not in html
    assert "vyplacejici" not in html


def test_analysis_and_report_share_identical_canonical_treaty_excerpt():
    client = TestClient(app)
    payload = _ad_dividend_payload()
    analysis = client.post("/analysis", json=payload).json()
    report = client.post("/analysis/report", json=payload).json()["report"]

    analysis_treaty = next(
        source
        for source in analysis["citations"]
        if source["legal_layer"] == "treaty"
    )
    report_treaty = next(
        source
        for source in report["official_sources"]
        if source["legal_layer"] == "treaty"
    )

    assert analysis_treaty["excerpt"] == report_treaty["excerpt"]
    assert analysis_treaty["excerpt_sha256"] == report_treaty["excerpt_sha256"]
    assert analysis_treaty["official_text"] == report_treaty["excerpt"]


def test_cz_interest_and_royalty_reports_include_section38nb_eligibility_snapshot():
    for income in ("interest", "royalty"):
        html = _cz_ir_domestic_exemption_html(
            {"scope": {"source_country": "CZ", "income_type": income}}
        )
        assert "Možné vnitrostátní osvobození" in html
        assert "§ 19 ZDP" in html
        assert "§ 38nb ZDP" in html
        assert "25% propojení" in html
        assert "24 měsíců" in html
        assert "skutečné vlastnictví" in html
        assert "stálé provozovně" in html

    assert _cz_ir_domestic_exemption_html(
        {"scope": {"source_country": "CZ", "income_type": "dividend"}}
    ) == ""
    assert _cz_ir_domestic_exemption_html(
        {"scope": {"source_country": "SK", "income_type": "interest"}}
    ) == ""
