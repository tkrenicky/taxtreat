from pathlib import Path

from taxtreat.services.source_country_capabilities import source_country_capability


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"


def _country_block(text: str, code: str) -> str:
    marker = f'{code}: Object.freeze({{'
    return text.split(marker, 1)[1].split('}),', 1)[0]


def test_public_web_country_contract_matches_cz_backend_release_currency_and_fx():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    backend = source_country_capability("CZ")
    block = _country_block(text, "CZ")

    assert f'baseCurrency: "{backend["currency"]}"' in block
    expected_fx = "null" if backend["fx_provider"] is None else f'"{backend["fx_provider"]}"'
    assert f'fxProvider: {expected_fx}' in block
    assert f'runtimeReleased: {str(backend["runtime_released"]).lower()}' in block
    assert f'availability: "{backend["availability"]}"' in block


def test_sk_backend_contract_exists_but_is_not_exposed_in_public_web_context():
    text = CONTEXT_JS.read_text(encoding="utf-8")
    backend = source_country_capability("SK")

    assert backend["runtime_released"] is True
    assert backend["currency"] == "EUR"
    assert backend["compliance"]["form_code"] == "OZN4311v26"

    assert 'SK: Object.freeze({' not in text
    assert 'code: "SK"' not in text
    assert 'OZN4311v26' not in text
    assert 'Slovensko' not in text
