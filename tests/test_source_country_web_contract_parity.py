from pathlib import Path

from taxtreat.services.source_country_capabilities import source_country_capability


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"


def _country_block(text: str, code: str) -> str:
    marker = f'{code}: Object.freeze({{'
    return text.split(marker, 1)[1].split('}),', 1)[0]


def test_web_country_contract_matches_backend_release_currency_and_fx():
    text = CONTEXT_JS.read_text(encoding="utf-8")

    for code in ("CZ", "SK"):
        backend = source_country_capability(code)
        block = _country_block(text, code)

        assert f'baseCurrency: "{backend["currency"]}"' in block
        expected_fx = "null" if backend["fx_provider"] is None else f'"{backend["fx_provider"]}"'
        assert f'fxProvider: {expected_fx}' in block
        assert f'runtimeReleased: {str(backend["runtime_released"]).lower()}' in block
        assert f'availability: "{backend["availability"]}"' in block


def test_slovak_web_contract_matches_backend_compliance_contract():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    block = _country_block(text, "SK")
    backend = source_country_capability("SK")
    compliance = backend["compliance"]

    assert f'complianceFormCode: "{compliance["form_code"]}"' in block
    assert compliance["legal_reference"] in block
    assert f'notificationPeriodicity: "{compliance["periodicity"]}"' in block
    assert 'notificationDeadlineRule: "15th_day_of_following_calendar_month"' in block
    assert 'remittanceDeadlineRule: "15th_day_of_following_calendar_month"' in block
    assert 'ordinaryAnnualWhtReturnConfigured: false' in block
    assert '586/1992' not in block
    assert 'CNB' not in block
