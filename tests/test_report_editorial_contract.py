from bs4 import BeautifulSoup

from taxtreat.services.reporting import render_report_html
from taxtreat.services.reporting.client_report import (
    _deadline_cards,
    _display_fact,
    _display_number,
    _extract_numbered_paragraph,
    _key_facts_html,
    _legal_reference,
    _operative_excerpt,
    _result_conclusion,
    _selected_source,
    _source_link,
    _transaction_gloss,
    _transaction_title,
    _treaty_name,
    _treaty_name_in_sentence,
    _truncate_at_boundary,
)


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
    assert "Jak se stanoví sazba" in html
    assert "Od českého pravidla ke konečné sazbě" in html
    assert "Česká srážková daň" in html and "SZDZ / osvobození" in html and "MLI / PPT" in html


def test_automation_wording_is_not_repeated_in_report_body():
    html = render_report_html(_sample_report())
    assert html.lower().count("automatizovaně") == 1


def test_client_report_helper_fallbacks_and_formats():
    assert _display_number(None) == "—"
    assert _display_number("abc") == "abc"
    assert _display_number(1234.5) == "1 234.5"
    assert _display_fact(False, "boolean") == "Ne"
    assert _display_fact(12.5, "percent") == "12.5 %"
    assert _display_fact(18, "months") == "18 měsíců"
    assert _display_fact("software", "text") == "software"

    report = {"scope": {"recipient_country": "ZZ", "income_type": "interest"}, "assumptions": {"transaction_facts": {}}}
    assert _transaction_title(report).startswith("Úroková platba: Plátce – název neuveden")
    assert _treaty_name(report) == "Smlouva o zamezení dvojího zdanění ČR–ZZ"
    assert _treaty_name_in_sentence(report) == "smlouvy o zamezení dvojího zdanění ČR–ZZ"
    assert _treaty_name({"scope": {}}) == "Smlouva o zamezení dvojího zdanění"


def test_client_report_source_selection_and_legal_reference_fallbacks():
    report = {"result": {"selected_rule_id": "missing"}, "scope": {"recipient_country": "AT"}}
    treaty = {"rule_id": "t", "legal_layer": "treaty", "article": "10", "paragraph": "2"}
    domestic = {"rule_id": "d", "legal_layer": "domestic", "article": "36", "paragraph": "1"}
    protocol = {"legal_layer": "protocol", "article": "1", "paragraph": "2"}
    mli = {"legal_layer": "mli", "article": "7", "paragraph": "1"}

    selected, rule_id = _selected_source(report, [domestic, treaty])
    assert selected is treaty and rule_id == "missing"
    selected, _ = _selected_source(report, [domestic])
    assert selected is domestic
    assert _legal_reference(report, None) == "—"
    assert "protokolu" in _legal_reference(report, protocol)
    assert "MLI" in _legal_reference(report, mli)
    assert "zákona č. 586/1992 Sb." in _legal_reference(report, domestic)
    assert _source_link(None) == ""


def test_client_report_excerpt_and_truncation_edge_cases():
    assert _extract_numbered_paragraph("", "2") == ""
    assert _extract_numbered_paragraph("Celý text bez číslování", "") == "Celý text bez číslování"
    assert _extract_numbered_paragraph("1. Jeden\n2. Dva", "3") == "1. Jeden\n2. Dva"
    assert _operative_excerpt(None) == "Právní výňatek není k dispozici."
    assert "není v reportu" in _operative_excerpt({"excerpt": "", "paragraph": "2"})

    long_with_boundary = ("První věta. " * 200).strip()
    cut = _truncate_at_boundary(long_with_boundary, 120)
    assert cut.endswith("… (dále zkráceno)")
    long_without_boundary = "x" * 80 + " " + "y" * 80
    cut2 = _truncate_at_boundary(long_without_boundary, 100)
    assert cut2.endswith("… (dále zkráceno)")


def test_client_report_result_deadline_gloss_and_key_fact_variants():
    report = _sample_report()
    treaty = report["official_sources"][0]

    nonfinal = _sample_report()
    nonfinal["result"] = {"status": "NEEDS_INFO"}
    assert "doplnit" in _result_conclusion(nonfinal, treaty, "—")

    exempt = _sample_report()
    exempt["result"]["tax_treatment"] = "domestic_exemption"
    assert "osvobození" in _result_conclusion(exempt, treaty, "0 %")

    numeric = _sample_report()
    numeric["result"]["tax_treatment"] = "treaty_rate"
    numeric["result"]["rate"] = 5
    assert "5 %" in _result_conclusion(numeric, treaty, "5 %")

    deadlines = _deadline_cards({"remittance_deadline": "2026-08-31", "notification_deadline": "2026-09-30"})
    assert "Odvod srážkové daně" in deadlines
    assert "Oznámení o příjmech" in deadlines

    plain = {"scope": {"income_type": "interest"}, "assumptions": {"transaction_facts": {}}}
    assert _transaction_gloss(plain).startswith("Použité ustanovení")
    key_facts = _key_facts_html("5 %", "interest", treaty, {})
    assert "Použitá sazba" in key_facts
    assert "Nejbližší uvedená lhůta" not in key_facts
