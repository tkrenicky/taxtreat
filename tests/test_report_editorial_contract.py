from bs4 import BeautifulSoup

from taxtreat.services.reporting import render_report_html


def _sample_report():
    return {
        "report_id": "TAXTREAT-TEST",
        "generated_at": "2026-08-17T10:00:00Z",
        "legal_data_cutoff": "2026-08-12",
        "legal_dataset_release": "test-release",
        "source_release": "test-source",
        "scope": {
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
            "transaction_date": "2026-08-17",
            "transaction_amount": {"amount": 1000000, "currency": "CZK"},
        },
        "assumptions": {
            "transaction_facts": {
                "report_payer_name": "Demo CZ s.r.o.",
                "report_recipient_name": "Demo GmbH",
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
                "permanent_establishment_connection": False,
                "ownership_percent": 25,
                "direct_ownership": True,
                "holding_period_months": 24,
            },
            "user_determinations": {},
        },
        "result": {
            "status": "FINAL",
            "rate": 0,
            "tax_treatment": "exclusive_foreign_taxation",
            "selected_rule_id": "treaty-at-dividend",
            "candidate_rule_id": None,
            "withholding_tax_calculation": {
                "status": "CALCULATED",
                "gross_amount_czk": 1000000,
                "withholding_tax_czk": 0,
            },
            "withholding_compliance_schedule": {},
        },
        "official_sources": [
            {
                "rule_id": "treaty-at-dividend",
                "source_id": "AT-DTT",
                "source_url": "https://example.test/treaty",
                "article": "10",
                "paragraph": "2",
                "legal_layer": "treaty",
                "legal_instrument": "CZ-AT DTT",
                "rate": 0,
                "excerpt": "Článek 10\n1. Test.\n2. Test treaty excerpt with 5 procent.\n3. Other text.",
            }
        ],
        "missing_facts": [],
        "required_documentation": [],
        "explanation": [],
        "disclaimer": "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace z právních zdrojů.",
    }


def test_report_uses_named_professional_czech_legal_reference():
    html = render_report_html(_sample_report())
    assert "Podle Smlouva" not in html
    assert "Smlouva mezi Českou republikou a Rakouskem o zamezení dvojího zdanění" in html
    assert "čl. 10 odst. 2 smlouvy mezi Českou republikou a Rakouskem" in html
    assert "příslušné smlouvy o zamezení dvojího zdanění" not in html
    assert "Skutkový bod" not in html
    assert "skutkový bod" not in html
    assert "přiřazenému výsledku" not in html


def test_report_is_two_page_client_document():
    html = render_report_html(_sample_report())
    assert "01 / 02" in html
    assert "02 / 02" in html
    assert "03 / 04" not in html
    assert "04 / 04" not in html
    assert "Použité ustanovení a praktické kroky" in html
    assert "Použité předpoklady" in html
    assert "Klíčové právní reference" not in html
    assert "Jak jsme k sazbě dospěli" not in html


def test_report_identifies_parties_and_marks_assumptions_as_user_supplied():
    html = render_report_html(_sample_report())
    assert "Výplata dividend: Demo CZ s.r.o. → Demo GmbH" in html
    assert "Skutečný vlastník příjmu" in html
    assert "Daňová rezidence pro účely smlouvy" in html
    assert "Vazba příjmu ke stálé provozovně v ČR" in html
    assert "Podíl na základním kapitálu plátce" in html
    assert "zadány uživatelem a nebyly nezávisle ověřeny" in html


def test_report_shows_only_operational_excerpt_and_net_amount():
    html = render_report_html(_sample_report())
    soup = BeautifulSoup(html, "html.parser")
    visible_quote = soup.select_one(".legal-source .quote")
    assert visible_quote is not None
    quote_text = visible_quote.get_text(" ", strip=True)
    assert quote_text.startswith("2. Test treaty excerpt with 5 procent")
    assert "1. Test." not in quote_text
    assert "3. Other text." not in quote_text
    assert "<strong>5 procent</strong>" in str(visible_quote)
    assert "Čistá částka po srážce" in html
    assert "1 000 000 Kč" in html


def test_client_report_hides_release_metadata_and_uses_one_language():
    html = render_report_html(_sample_report())
    assert "Právní stav" not in html
    assert "Dataset" not in html
    assert "test-release" not in html
    assert "test-source" not in html
    assert "Result available" not in html
    assert "Additional information required" not in html
    assert "Applicable WHT rate" not in html
    assert "Transaction details" not in html
    assert "Decision path" not in html
    assert "Report details" not in html
    assert "Výsledek k dispozici" not in html
    assert "Výsledek srážkové daně" not in html


def test_client_report_uses_restrained_visual_contract():
    html = render_report_html(_sample_report())
    assert "<svg" not in html
    assert "hero-art" not in html
    assert "linear-gradient" not in html
    assert "Následující údaje byly zadány uživatelem" in html
    assert "Údaje k doplnění" not in html


def test_automation_wording_is_not_repeated_in_report_body():
    html = render_report_html(_sample_report())
    assert html.lower().count("automatizovaně") == 1
