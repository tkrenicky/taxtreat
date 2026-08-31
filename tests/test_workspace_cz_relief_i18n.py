from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "app" / "web" / "workspace-report-export.js"
ENHANCEMENT = ROOT / "app" / "web" / "workspace-cz-relief-i18n.js"
SOURCE_ADAPTER = ROOT / "app" / "web" / "workspace-source-country-adapter.js"
PAYER_COUNTRY = ROOT / "app" / "web" / "workspace-payer-country.js"
FINAL_POLISH = ROOT / "app" / "web" / "workspace-final-polish-v2.js"
REPORT_CONTEXT = ROOT / "app" / "web" / "workspace-report-context.js"


def test_workspace_loads_enhancements_in_safe_order_before_report_core():
    text = LOADER.read_text(encoding="utf-8")
    for script in (
        "workspace-cz-relief-i18n.js",
        "source-country-context.js",
        "workspace-source-country-adapter.js",
        "workspace-payer-country.js",
        "workspace-final-polish-v2.js",
        "workspace-report-context.js",
        "workspace-report-export-core.js",
    ):
        assert script in text
    assert text.index("workspace-cz-relief-i18n.js") < text.index("workspace-source-country-adapter.js")
    assert text.index("workspace-source-country-adapter.js") < text.index("workspace-payer-country.js")
    assert text.index("workspace-payer-country.js") < text.index("workspace-final-polish-v2.js")
    assert text.index("workspace-final-polish-v2.js") < text.index("workspace-report-context.js")
    assert text.index("workspace-report-context.js") < text.index("workspace-report-export-core.js")


def test_czech_dividend_section19_facts_are_sent_to_engine():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    for fact in (
        "recipient_is_qualifying_company_form",
        "recipient_is_tax_resident_in_eligible_jurisdiction",
        "recipient_subject_to_qualifying_corporate_tax",
        "recipient_has_no_tax_exemption_or_zero_rate_option",
        "recipient_is_parent_company",
    ):
        assert fact in text
    assert 'payload.income_type !== "dividend"' in text
    assert 'String(payload.source_country || "").toUpperCase() !== "CZ"' in text


def test_section19_questions_are_plain_facts_not_legal_conclusions():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Ještě dva údaje pro možné osvobození" in text
    assert "běžnou obchodní společností" in text
    assert "běžné dani z příjmů právnických osob" in text
    assert "recipient_is_parent_company = Boolean" in text
    assert "Splňuje příjemce postavení mateřské společnosti" not in text
    assert "Je příjemce kvalifikovanou společností v přípustné právní formě" not in text


def test_section19_unknown_answers_are_fail_closed_not_false():
    text = FINAL_POLISH.read_text(encoding="utf-8")
    assert 'option.value = "unknown"' in text
    assert "Nevím / potřebuji ověřit" in text
    assert "zvol raději „Ne“" not in text


def test_section19_is_visible_in_result_and_precedes_treaty_conclusion():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Vnitrostátní osvobození" in text
    assert "Primárním právním titulem je § 19 ZDP" in text
    assert "§ 19 byl posouzen před smluvní úlevou" in text
    assert "reason.before(box)" in text


def test_interest_and_royalty_exemption_is_informational_only():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Možné vnitrostátní osvobození" in text
    assert "§ 38nb ZDP" in text
    assert '["interest", "royalty"].includes(resultIncomeType())' in text
    assert "section_38nb_decision_effective" not in text


def test_only_web_language_control_is_in_header_and_report_language_is_by_export():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "taxtreat-ui-language" in text
    assert "taxtreat-report-language" in text
    assert 'const actions = document.querySelector(\'.flow-step[data-step="4"] .flow-actions\')' in text
    assert 'label.id = "taxtreat-language-controls"' in text
    assert "Jazyk reportu" in text
    assert "translateReportHtml" in text


def test_payer_and_section19_polish_is_bilingual():
    text = FINAL_POLISH.read_text(encoding="utf-8")
    assert '"Stát plátce *", "Payer country *"' in text
    assert '"Jazyk reportu", "Report language"' in text
    assert '"Nevím / potřebuji ověřit", "I don\'t know / needs verification"' in text


def test_source_country_is_payer_derived_and_not_user_selectable():
    text = SOURCE_ADAPTER.read_text(encoding="utf-8")
    assert "inferredCountryForActivePayer" in text
    assert 'activePayerSelect.addEventListener("change"' in text
    assert 'countryControl.hidden = true' in text
    assert "setPayerCountry" in text
    assert "getPayerCountry" in text


def test_payer_editor_contains_country_fact_and_handles_dynamic_edit_dialog():
    text = PAYER_COUNTRY.read_text(encoding="utf-8")
    assert "Stát plátce *" in text
    assert '<option value="CZ">${en ? "Czech Republic" : "Česká republika"}</option>' in text
    assert '<option value="SK">${en ? "Slovakia" : "Slovensko"}</option>' in text
    assert "určuje, která vnitrostátní pravidla srážkové daně" in text
    assert "setPayerCountry" in text
    assert "ARES" in text
    assert 'attributeFilter: ["open"]' in text
    assert "refreshPayerCountryCopy" in text


def test_report_regeneration_preserves_section19_facts_and_report_language():
    text = REPORT_CONTEXT.read_text(encoding="utf-8")
    assert 'url.endsWith("/analysis/report")' in text
    assert "__report_language" in text
    assert "recipient_is_qualifying_company_form" in text
    assert "recipient_is_tax_resident_in_eligible_jurisdiction" in text
    assert "recipient_subject_to_qualifying_corporate_tax" in text
    assert "recipient_is_parent_company" in text
