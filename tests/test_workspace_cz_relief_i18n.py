from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "app" / "web" / "workspace-report-export.js"
ENHANCEMENT = ROOT / "app" / "web" / "workspace-cz-relief-i18n.js"


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
    assert 'String(payload.source_country).toUpperCase() !== "CZ"' in text


def test_interest_and_royalty_exemption_is_informational_only():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "Možné vnitrostátní osvobození" in text
    assert "§ 38nb ZDP" in text
    assert 'includes(state.lastIncomeType)' in text
    assert "section_38nb_decision_effective" not in text


def test_web_and_report_languages_are_independent():
    text = ENHANCEMENT.read_text(encoding="utf-8")
    assert "taxtreat-ui-language" in text
    assert "taxtreat-report-language" in text
    assert "taxtreat-ui-language\") || \"cs\"" in text
    assert "taxtreat-report-language\") || \"cs\"" in text
    assert "translateReportHtml" in text
