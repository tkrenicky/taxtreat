from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_JS = ROOT / "app" / "web" / "source-country-context.js"
ADAPTER_JS = ROOT / "app" / "web" / "workspace-source-country-adapter.js"
SK_BACKEND = ROOT / "taxtreat" / "countries" / "sk.py"


def test_public_workspace_exposes_released_cz_and_sk_contexts():
    text = CONTEXT_JS.read_text(encoding="utf-8")

    assert 'code: "CZ"' in text
    assert 'baseCurrency: "CZK"' in text
    assert 'fxProvider: "CNB"' in text

    assert 'SK: Object.freeze({' in text
    assert 'code: "SK"' in text
    assert 'baseCurrency: "EUR"' in text
    assert 'fxProvider: "ECB/NBS"' in text
    assert 'runtimeReleased: true' in text
    assert 'OZN4311v26' in text
    assert 'Slovenská zrážková daň' in text
    assert 'scopeValue: "225"' in text


def test_public_workspace_offers_cz_sk_source_country_switching():
    adapter = ADAPTER_JS.read_text(encoding="utf-8")

    assert '<option value="CZ">Česká republika</option>' in adapter
    assert '<option value="SK">Slovensko</option>' in adapter
    assert 'countryControl.hidden = true;' not in adapter
    assert 'applyContext("CZ")' in adapter


def test_public_workspace_rejects_unknown_source_country_context():
    text = CONTEXT_JS.read_text(encoding="utf-8")

    assert 'Unsupported source country' in text
    assert 'function getSourceCountryContext(code)' in text


def test_sk_backend_package_remains_in_repository():
    text = SK_BACKEND.read_text(encoding="utf-8")

    assert 'def evaluate_domestic_precedence(' in text
    assert 'OUTSIDE_SUBJECT_OF_TAX' in text
    assert '§ 12 ods. 7 písm. c)' in text
