from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "app" / "web" / "workspace-report-export.js"
ENHANCEMENT = ROOT / "app" / "web" / "workspace-cz-relief-i18n.js"
SOURCE_ADAPTER = ROOT / "app" / "web" / "workspace-source-country-adapter.js"


def test_workspace_loads_czech_relief_and_language_layer_before_report_core():
    text = LOADER.read_text(encoding="utf-8")
    assert "workspace-cz-relief-i18n.js" in text
    assert text.index("workspace-cz-relief-i18n.js") < text.index("workspace-report-export-core.js")


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
    assert "Ještě dva údaje pro možné osvobození podle § 19 ZDP" in text
    assert "běžnou obchodní společností" in text
    assert "běžné dani z příjmů právnických osob" in text
    assert "recipient_is_parent_company = Boolean" in text
    assert "Splňuje příjemce postavení mateřské společnosti" not in text
    assert "Je příjemce kvalifikovanou společností v přípustné právní formě" not in text


def test_section19_is_visible_in_result_and_precedes_treaty_conclusion():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Vnitrostátní osvobození podle § 19 ZDP" in text
    assert "Primárním právním titulem je § 19 ZDP" in text
    assert "§ 19 se posuzuje před smluvní úlevou" in text


def test_interest_and_royalty_exemption_is_informational_only():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Možné vnitrostátní osvobození" in text
    assert "§ 38nb ZDP" in text
    assert 'includes(state.lastIncomeType)' in text
    assert "section_38nb_decision_effective" not in text


def test_only_web_language_control_is_in_header_and_report_language_is_by_export():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "taxtreat-ui-language" in text
    assert "taxtreat-report-language" in text
    assert 'const actions = document.querySelector(\'.flow-step[data-step="4"] .flow-actions\')' in text
    assert 'label.id = "taxtreat-language-controls"' in text
    assert "translateReportHtml" in text


def test_source_country_is_payer_derived_and_not_user_selectable():
    text = SOURCE_ADAPTER.read_text(encoding="utf-8")
    assert "inferredCountryForActivePayer" in text
    assert 'activePayerSelect.addEventListener("change"' in text
    assert "active-source-country" not in text
    assert "setPayerCountry" in text
