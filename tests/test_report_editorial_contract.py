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
                "excerpt": "Test treaty excerpt.",
            }
        ],
        "missing_facts": [],
        "required_documentation": [],
        "explanation": [],
        "disclaimer": "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace z právních zdrojů.",
    }


def test_report_uses_professional_czech_legal_reference():
    html = render_report_html(_sample_report())
    assert "Podle Smlouva" not in html
    assert "Podle čl. 10 odst. 2 příslušné smlouvy o zamezení dvojího zdanění" in html
    assert "Skutkový bod" not in html
    assert "skutkový bod" not in html


def test_report_is_four_page_client_document():
    html = render_report_html(_sample_report())
    assert "01 / 04" in html
    assert "02 / 04" in html
    assert "03 / 04" in html
    assert "04 / 04" in html
    assert "Právní zdroje" in html
    assert "Použité předpoklady" in html
    assert "Klíčové právní reference" not in html


def test_report_identifies_parties_and_assumptions():
    html = render_report_html(_sample_report())
    assert "Výplata dividend: Demo CZ s.r.o. → Demo GmbH" in html
    assert "Skutečný vlastník příjmu" in html
    assert "Daňová rezidence pro účely smlouvy" in html
    assert "Vazba příjmu ke stálé provozovně v ČR" in html
    assert "Podíl na základním kapitálu plátce" in html


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


def test_automation_wording_is_not_repeated_in_report_body():
    html = render_report_html(_sample_report())
    assert html.lower().count("automatizovaně") == 1
