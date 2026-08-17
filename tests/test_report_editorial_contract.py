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


def test_report_is_four_page_editorial_document():
    html = render_report_html(_sample_report())
    assert "01 / 04" in html
    assert "02 / 04" in html
    assert "03 / 04" in html
    assert "04 / 04" in html
    assert "Právní základ a oficiální zdroje" in html
    assert "Klíčové právní reference" in html


def test_automation_wording_is_not_repeated_in_report_body():
    html = render_report_html(_sample_report())
    assert html.lower().count("automatizovaně") == 1
