from taxtreat.services.reporting import render_report_html


def _final_sk_report():
    return {
        "scope": {
            "source_country": "SK",
            "recipient_country": "US",
            "income_type": "royalty",
            "transaction_date": "2026-08-19",
            "transaction_amount": {"amount": "1000", "currency": "USD"},
        },
        "result": {
            "status": "FINAL",
            "rate": 10,
            "tax_treatment": "taxable_at_rate",
            "selected_rule_id": "SK-US-royalty-test",
            "candidate_rule_id": None,
            "withholding_tax_calculation": {
                "source_country": "SK",
                "status": "CALCULATED",
                "gross_amount": "1000",
                "transaction_currency": "USD",
                "tax_currency": "EUR",
                "rate_percent": "10",
                "withholding_tax_transaction_currency": "100.00",
                "withholding_tax_eur": "86.27",
                "exchange_rate": {
                    "source": "ECB",
                    "currency": "USD",
                    "foreign_units_per_eur": "1.1591",
                    "effective_date": "2026-08-19",
                    "source_url": "https://nbs.sk/statisticke-udaje/kurzovy-listok/denny-kurzovy-listok-ecb/",
                },
            },
            "withholding_compliance_schedule": {
                "source_country": "SK",
                "status": "READY",
                "tax_remittance_deadline": "2026-09-15",
                "notification_deadline": "2026-09-15",
            },
        },
        "assumptions": {
            "transaction_facts": {
                "report_payer_name": "SK Payer s.r.o.",
                "report_recipient_name": "US Recipient Inc.",
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
            }
        },
        "missing_facts": [],
        "official_sources": [{
            "rule_id": "SK-US-royalty-test",
            "legal_layer": "treaty",
            "article": "12",
            "paragraph": "2",
            "rate": 10,
            "source_url": "https://static.slov-lex.sk/",
            "excerpt": "10 percent",
        }],
        "disclaimer": "TaxTreat je informační nástroj a neurčuje postup uživatele.",
    }


def test_final_sk_report_renders_payment_currency_tax_eur_and_ecb_quote():
    html = render_report_html(_final_sk_report())
    assert "1 000 USD" in html
    assert "86.27 EUR" in html
    assert "900 USD" in html
    assert "1 EUR = 1.1591 USD" in html
    assert "Kurz ECB" in html
    assert "Kurzovní lístek ČNB" not in html
    assert " Kč" not in html
    assert "CZK" not in html
