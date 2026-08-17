from bs4 import BeautifulSoup

from taxtreat.services.reporting import render_report_html


def _report():
    return {
        "generated_at": "2026-08-17T20:00:00Z",
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
                "ownership_percent": 100,
                "direct_ownership": True,
                "holding_period_months": 24,
            }
        },
        "result": {
            "status": "FINAL",
            "rate": 5,
            "tax_treatment": "treaty_rate",
            "selected_rule_id": "at-dividend",
            "withholding_tax_calculation": {
                "status": "CALCULATED",
                "gross_amount_czk": 1000000,
                "withholding_tax_czk": 50000,
                "net_amount_czk": 950000,
            },
            "withholding_compliance_schedule": {
                "remittance_deadline": "2026-09-30",
                "notification_deadline": "2026-09-30",
            },
        },
        "official_sources": [
            {
                "rule_id": "domestic-dividend",
                "source_id": "ZDP",
                "source_url": "https://www.zakonyprolidi.cz/cs/1992-586",
                "article": "36",
                "paragraph": "1",
                "legal_layer": "domestic",
                "rate": 15,
                "excerpt": "§ 36 odst. 1",
            },
            {
                "rule_id": "at-dividend",
                "source_id": "AT-DTT",
                "source_url": "https://www.e-sbirka.cz/",
                "article": "10",
                "paragraph": "2",
                "legal_layer": "treaty",
                "rate": 5,
                "excerpt": "Článek 10\n1. Test.\n2. Test treaty excerpt with 5 procent.\n3. Other text.",
            },
        ],
        "missing_facts": [],
        "disclaimer": "TaxTreat je informační nástroj. Automatizovaně zobrazuje informace z právních zdrojů.",
    }


def test_round3_copy_polish_is_applied():
    html = render_report_html(_report())
    assert "anti-abuse test" not in html
    assert "test hlavního účelu (PPT)" in html
    assert "Vzniká česká srážková daň? Jaký je její výchozí režim?" in html
    assert "Nejbližší uvedená lhůta" not in html
    assert "Nejbližší lhůta" in html
    assert "Lhůta pro odvod daně plátcem." not in html
    assert "Plátce je povinen sraženou daň odvést správci daně nejpozději do tohoto data." in html
    assert "Pro použitou sazbu byly zohledněny zejména" not in html
    assert "Použitá sazba vychází z těchto zadaných údajů:" in html


def test_round3_disclaimer_is_restored_in_full():
    html = render_report_html(_report())
    assert "Neprovádí individuální právní ani daňové posouzení" in html
    assert "neposkytuje doporučení ani právní či daňové poradenství" in html
    assert "Uživatel odpovídá za správnost vstupních údajů" in html
    assert html.lower().count("automatizovaně") == 1


def test_round3_flow_is_timeline_without_duplicate_principle():
    html = render_report_html(_report())
    soup = BeautifulSoup(html, "html.parser")
    assert soup.select_one(".flow") is not None
    assert len(soup.select(".flow-node")) == 5
    assert soup.select_one(".flow-principle") is None
    assert "grid-template-columns: repeat(5, minmax(0, 1fr))" in html
    assert ".flow::before" in html
    assert "display: none !important" in html
