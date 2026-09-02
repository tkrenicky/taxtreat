from pathlib import Path

from taxtreat.services.source_country_capabilities import source_country_capability

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"


def _country_block(text: str, code: str) -> str:
    marker = f'{code}: Object.freeze({{'
    return text.split(marker, 1)[1].split('}),', 1)[0]


def _assert_backend_parity(code: str):
    text = CONTEXT_JS.read_text(encoding="utf-8")
    backend = source_country_capability(code)
    block = _country_block(text, code)

    assert f'baseCurrency: "{backend["currency"]}"' in block
    expected_fx = "null" if backend["fx_provider"] is None else f'"{backend["fx_provider"]}"'
    assert f'fxProvider: {expected_fx}' in block
    assert f'runtimeReleased: {str(backend["runtime_released"]).lower()}' in block
    assert f'availability: "{backend["availability"]}"' in block


def test_public_web_cz_contract_matches_backend():
    _assert_backend_parity("CZ")


def test_public_web_sk_contract_matches_backend_and_compliance_release():
    _assert_backend_parity("SK")
    text = CONTEXT_JS.read_text(encoding="utf-8")
    block = _country_block(text, "SK")
    backend = source_country_capability("SK")

    assert backend["runtime_released"] is True
    assert backend["currency"] == "EUR"
    assert backend["compliance"]["form_code"] == "OZN4311v26"
    assert 'complianceFormCode: "OZN4311v26"' in block
    assert 'notificationDeadlineRule: "15th_day_of_following_calendar_month"' in block
    assert 'remittanceDeadlineRule: "15th_day_of_following_calendar_month"' in block
