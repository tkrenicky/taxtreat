from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"
WORKSPACE = WEB / "workspace.js"
HTML = WEB / "workspace.html"
CZ_RELIEF = WEB / "workspace-cz-relief-i18n.js"
SOURCE_ADAPTER = WEB / "workspace-source-country-adapter.js"
PAYER_COUNTRY = WEB / "workspace-payer-country.js"
REPORT_CONTEXT = WEB / "workspace-report-context.js"


def test_workspace_contains_section19_relief_controls_and_copy():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert "§ 19 odst. 1 písm. ze)" in text
    assert "section19_company_form" in text
    assert "section19_tax_residency" in text
    assert "section19_taxable_company" in text
    assert "section19_parent_company" in text
    assert "section19_holding_period" in text
    assert "section19_future_holding" in text
    assert "section19_corporate_tax" in text
    assert "section19_no_exemption" in text


def test_workspace_payload_contains_section19_facts():
    text = WORKSPACE.read_text(encoding="utf-8")
    assert "recipient_is_qualifying_company_form" in text
    assert "recipient_is_tax_resident_in_eligible_jurisdiction" in text
    assert "recipient_subject_to_qualifying_corporate_tax" in text
    assert "recipient_is_parent_company" in text
    assert "recipient_holds_required_ownership" in text
    assert "recipient_meets_minimum_holding_period" in text
    assert "recipient_will_meet_minimum_holding_period" in text
    assert "recipient_has_no_tax_exemption_or_zero_rate_option" in text


def test_section19_controls_are_dividend_only():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert "syncSection19Visibility" in text
    assert "income_type" in text
    assert 'field.required = isCz && document.querySelector(\'#workspace-payment [name="income_type"]\')?.value === "dividend"' in text


def test_cz_domestic_relief_has_clear_priority_copy():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert "vnitrostátní osvobození" in text
    assert "před smlouvou" in text


def test_cz_relief_copy_is_localized():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert "Czech domestic exemption" in text
    assert "domestic exemption" in text


def test_section19_state_survives_runtime_language_changes():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert "applyUiLanguage" in text
    assert "taxtreat:language-changed" in text


def test_section19_controls_are_hidden_for_sk_source_country():
    text = CZ_RELIEF.read_text(encoding="utf-8")
    assert 'body[data-source-country="SK"] #cz-section19-facts' in text
    assert "display: none !important" in text


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
    assert '<option value="CZ">🇨🇿 ${en ? "Czech Republic" : "Česká republika"}</option>' in text
    assert '<option value="SK">🇸🇰 ${en ? "Slovakia" : "Slovensko"}</option>' in text
    assert "určuje, která vnitrostátní pravidla srážkové daně" in text
    assert "setPayerCountry" in text
    assert "ARES" in text
    assert 'attributeFilter: ["open"]' in text
    assert "refreshPayerCountryCopy" in text
    assert "active-payer-country-badge" in text
    assert "payer-country-flag" in text
    assert "taxtreat:source-country-change" in text
    assert "🇨🇿" in text and "🇸🇰" in text


def test_report_regeneration_preserves_section19_facts_and_report_language():
    text = REPORT_CONTEXT.read_text(encoding="utf-8")
    assert 'url.endsWith("/analysis/report")' in text
    assert "__report_language" in text
    assert "recipient_is_qualifying_company_form" in text
    assert "recipient_is_tax_resident_in_eligible_jurisdiction" in text
    assert "recipient_subject_to_qualifying_corporate_tax" in text
    assert "recipient_is_parent_company" in text
