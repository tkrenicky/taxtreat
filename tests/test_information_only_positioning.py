from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


FORBIDDEN_PUBLIC_PHRASES = (
    "ověřte s daňovým poradcem",
    "Ověřte s daňovým poradcem",
    "Ověřit s poradcem",
    "OVĚŘIT S PORADCEM",
    "doporučujeme projednat",
    "Odborné ověření",
    "ODBORNÉ OVĚŘENÍ",
    "Otevřít profesionální report",
    "mechanický výpočet",
    "mechanického výpočtu",
)


def _assert_information_only(text: str) -> None:
    for phrase in FORBIDDEN_PUBLIC_PHRASES:
        assert phrase not in text, f"Advisory-facing phrase leaked into public UI: {phrase}"


def test_public_ui_uses_information_only_positioning():
    legacy_html = client.get("/ui").text
    workspace_html = client.get("/workspace-demo").text
    legacy_js = client.get("/ui-assets/app.js").text
    workspace_js = client.get("/ui-assets/workspace.js").text
    export_js = client.get("/ui-assets/workspace-report-export.js").text

    for text in (legacy_html, workspace_html, legacy_js, workspace_js, export_js):
        _assert_information_only(text)

    assert "informační" in legacy_html.lower()
    assert "neposkytuje individuální daňové nebo právní poradenství" in legacy_html.lower()
    assert "Informační nástroj" in workspace_html
    assert "neposkytuje individuální daňové nebo právní poradenství" in workspace_html.lower()


def test_report_is_presented_as_information_not_individual_tax_advice():
    payload = {
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
        "transaction_amount": {
            "amount": "100000",
            "currency": "CZK",
            "payment_date": "2026-08-16",
            "accounting_date": "2026-08-16",
        },
    }
    response = client.post("/analysis/report", json=payload)
    assert response.status_code == 200
    html = response.json()["html"]

    _assert_information_only(html)
    assert "Informace k české srážkové dani" in html
    assert "Pravidlo přiřazené k zadaným údajům" in html
    assert "Použité právní pravidlo" in html
    assert "TaxTreat je informační nástroj" in html
    assert "neposkytuje doporučení ani právní či daňové poradenství" in html
    assert "<span>Závěr</span>" not in html
    assert "Posouzení srážkové daně" not in html
