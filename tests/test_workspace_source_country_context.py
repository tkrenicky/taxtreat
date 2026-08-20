from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"


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

    sk_block = text.split('SK: Object.freeze({', 1)[1].split('}),', 1)[0]
    assert 'baseCurrency: "EUR"' in sk_block
    assert 'fxProvider: "ECB/NBS"' in sk_block
    assert 'CNB' not in sk_block
    assert '586/1992' not in sk_block
    assert '38da' not in sk_block


def test_workspace_source_country_context_exposes_released_sk():
    text = CONTEXT_JS.read_text(encoding="utf-8")

    assert 'function finalAnalysisAllowed(code)' in text
    assert 'runtimeReleased === true' in text
    assert 'availability: "released"' in text


def test_workspace_source_country_context_carries_sk_monthly_compliance_timing():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    sk_block = text.split('SK: Object.freeze({', 1)[1].split('}),', 1)[0]

    assert 'notificationPeriodicity: "monthly"' in sk_block
    assert 'notificationDeadlineRule: "15th_day_of_following_calendar_month"' in sk_block
    assert 'remittanceDeadlineRule: "15th_day_of_following_calendar_month"' in sk_block
    assert 'ordinaryAnnualWhtReturnConfigured: false' in sk_block
