from taxtreat.services.reporting import render_report_html


def _sk_report():
    return {
        "scope": {
            "source_country": "SK",
            "recipient_country": "AT",
            "income_type": "interest",
            "transaction_date": "2026-08-19",
            "transaction_amount": {"amount": "1000", "currency": "EUR"},
        },
        "result": {
            "status": "REVIEW_REQUIRED",
            "rate": None,
            "candidate_rate": 10,
            "tax_treatment": None,
            "candidate_tax_treatment": None,
            "selected_rule_id": None,
            "candidate_rule_id": "SK-AT-interest-candidate",
            "withholding_tax_calculation": {
                "source_country": "SK",
                "status": "NOT_CALCULATED",
                "gross_amount": "1000",
                "transaction_currency": "EUR",
                "tax_currency": "EUR",
                "reason": "final_rate_unavailable",
            },
            "withholding_compliance_schedule": {
                "source_country": "SK",
                "status": "PENDING_FINAL_TREATMENT",
                "reference_date": "2026-08-19",
                "notification_deadline": None,
                "tax_remittance_deadline": None,
                "notification_form": "OZN4311v26",
                "notification_legal_basis": "§ 43 ods. 11 zákona č. 595/2003 Z. z.",
            },
        },
        "assumptions": {
            "transaction_facts": {
                "report_payer_name": "SK Payer s.r.o.",
                "report_recipient_name": "AT Recipient GmbH",
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
                "permanent_establishment_connection": False,
            }
        },
        "missing_facts": ["holding_period_months"],
        "official_sources": [
            {
                "rule_id": "SK-AT-interest-candidate",
                "legal_layer": "domestic",
                "article": "§ 43",
                "paragraph": "11",
                "source_url": "https://static.slov-lex.sk/static/SK/ZZ/2003/595/20260101.print.html",
                "excerpt": "§ 43 ods. 11",
            }
        ],
        "disclaimer": "TaxTreat je informační nástroj a neurčuje postup uživatele.",
    }


def test_real_sk_report_render_has_no_czech_source_country_legal_markers():
    html = render_report_html(_sk_report())

    assert '<html lang="sk">' in html
    assert "Informácie k slovenskej zrážkovej dani" in html
    assert "Sadzba slovenskej zrážkovej dane" in html
    assert "Slovenská zrážková daň" in html
    assert ">Platiteľ<" in html
    assert ">Príjemca<" in html
    assert "Slovenská vnútroštátna úprava" in html
    assert "slovenské právo zdaniť" in html
    assert "595/2003 Z. z." in html
    assert "Informace k české srážkové dani" not in html
    assert "Sazba české srážkové daně" not in html
    assert "Česká srážková daň" not in html
    assert "Od českého pravidla" not in html
    assert "Česká vnitrostátní úprava" not in html
    assert "české právo zdanit" not in html
    assert ">Plátce<" not in html
    assert ">Příjemce<" not in html
    assert "586/1992" not in html
    assert "§ 38da" not in html
    assert "§ 38d " not in html
    assert "Kurzovní lístek ČNB" not in html


def test_sk_report_localization_fails_closed_on_new_czech_legal_marker():
    from taxtreat.services.reporting.html_localization import localize_report_html
    import pytest

    # This is deliberately not one of the known replacement strings. It proves
    # the post-render guard catches a newly introduced Czech-law marker rather
    # than merely translating a phrase the table already knows about.
    with pytest.raises(ValueError, match="Czech-source-country legal leakage"):
        localize_report_html(
            "Nová šablona: § 38da neočekávaný text.",
            {"scope": {"source_country": "SK"}},
        )
