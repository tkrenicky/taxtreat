from taxtreat.services.reporting.localized_context import build_localized_report_context


def _report(source_country: str = "SK"):
    return {
        "scope": {
            "source_country": source_country,
            "recipient_country": "AT",
            "income_type": "interest",
        },
        "assumptions": {
            "transaction_facts": {
                "report_payer_name": "SK Payer s.r.o.",
                "report_recipient_name": "AT Recipient GmbH",
                "beneficial_owner": True,
            }
        },
        "result": {
            "withholding_compliance_schedule": {
                "remittance_deadline": "2026-09-15",
                "notification_deadline": "2026-09-15",
            }
        },
    }


def test_sk_report_context_is_country_specific():
    context = build_localized_report_context(_report())

    assert context.source_country == "SK"
    assert context.copy.language == "sk"
    assert context.copy.withholding_tax_label == "Slovenská zrážková daň"
    assert context.copy.permanent_establishment_fact_label.endswith("v SR")
    assert "595/2003 Z. z." in context.domestic_reference
    assert "586/1992" not in context.domestic_reference
    assert context.copy.official_source_label == "Oficiálny zdroj"
    assert context.copy.yes_label == "Áno"
    assert context.copy.no_label == "Nie"


def test_sk_compliance_copy_never_reuses_czech_section_38da():
    context = build_localized_report_context(_report())
    rendered = " ".join(
        [
            *(label + " " + note for label, note in context.deadline_cards),
            *(title + " " + question for title, question in context.flow_nodes),
        ]
    )

    assert "§ 43 ods. 11" in rendered
    assert "15. dňa nasledujúceho kalendárneho mesiaca" in rendered
    assert "§ 38da" not in rendered
    assert "česk" not in rendered.lower()


def test_sk_mli_copy_is_not_ppt_only():
    context = build_localized_report_context(_report())
    mli = next(
        question
        for title, question in context.flow_nodes
        if title == "MLI / PPT a ďalšie modifikácie"
    )

    assert "všetky párovo uplatniteľné modifikácie" in mli
    assert "dividendy" in mli
    assert "stálu prevádzkareň" in mli


def test_sk_report_documentation_uses_slovak_wording():
    context = build_localized_report_context(_report())
    joined = " ".join(context.documentation_items)

    assert "Potvrdenie o daňovej rezidencii" in joined
    assert "skutočného vlastníka" in joined
    assert "Zmluvná a platobná dokumentácia" in joined
    assert "Potvrzení" not in joined


def test_cz_copy_is_preserved_for_existing_renderer_migration():
    context = build_localized_report_context(_report("CZ"))

    assert context.source_country == "CZ"
    assert context.copy.withholding_tax_label == "Česká srážková daň"
    assert "586/1992 Sb." in context.domestic_reference
    assert any("§ 38da ZDP" in label for label, _ in context.deadline_cards)
