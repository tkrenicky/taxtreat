from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"
ADAPTER_JS = ROOT / "app" / "web" / "workspace-source-country-adapter.js"


def _sk_block(text: str) -> str:
    start = text.index('SK: Object.freeze({')
    end = text.index(
        '\n  });\n\n  const TAX_TREATMENT_PRESENTATION',
        start,
    )
    return text[start:end]


def test_workspace_source_country_context_distinguishes_cz_and_sk():
    text = CONTEXT_JS.read_text(encoding="utf-8")

    assert 'code: "CZ"' in text
    assert 'baseCurrency: "CZK"' in text
    assert 'fxProvider: "CNB"' in text
    assert 'runtimeReleased: true' in text

    assert 'code: "SK"' in text
    assert 'baseCurrency: "EUR"' in text
    assert 'fxProvider: "ECB/NBS"' in text
    assert text.count('runtimeReleased: true') >= 2
    assert 'complianceFormCode: "OZN4311v26"' in text
    assert '§ 43 ods. 11 zákona č. 595/2003 Z. z.' in text
    assert 'Slovenská zrážková daň' in text


def test_workspace_source_country_context_has_no_czech_fx_fallback_for_sk():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    sk_block = _sk_block(text)

    assert 'baseCurrency: "EUR"' in sk_block
    assert 'fxProvider: "ECB/NBS"' in sk_block
    assert 'CNB' not in sk_block
    assert '586/1992' not in sk_block
    assert '38da' not in sk_block


def test_workspace_source_country_context_exposes_released_sk():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    adapter = ADAPTER_JS.read_text(encoding="utf-8")
    sk_block = _sk_block(text)

    assert 'function finalAnalysisAllowed(code)' in text
    assert 'runtimeReleased === true' in text
    assert 'availability: "released"' in sk_block
    assert 'prereleaseNotice: ""' in sk_block
    assert 'technickom pre-release' not in sk_block
    assert 'před vydáním' not in adapter
    assert '<option value="SK">Slovensko</option>' in adapter


def test_workspace_source_country_context_carries_sk_monthly_compliance_timing():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    sk_block = _sk_block(text)

    assert 'notificationPeriodicity: "monthly"' in sk_block
    assert 'notificationDeadlineRule: "15th_day_of_following_calendar_month"' in sk_block
    assert 'remittanceDeadlineRule: "15th_day_of_following_calendar_month"' in sk_block
    assert 'ordinaryAnnualWhtReturnConfigured: false' in sk_block
