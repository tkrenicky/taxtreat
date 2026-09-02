from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"
CONTEXT = WEB / "source-country-context.js"
ADAPTER = WEB / "workspace-source-country-adapter.js"


def test_workspace_bootstrap_loads_country_context_and_adapter_before_existing_export_core():
    bootstrap = (WEB / "workspace-report-export.js").read_text(encoding="utf-8")

    country = "/ui-assets/source-country-context.js"
    adapter = "/ui-assets/workspace-source-country-adapter.js"
    core = "/ui-assets/workspace-report-export-core.js"

    assert country in bootstrap
    assert adapter in bootstrap
    assert core in bootstrap
    assert bootstrap.index(country) < bootstrap.index(adapter) < bootstrap.index(core)


def test_workspace_existing_report_export_logic_is_preserved_as_core():
    core = (WEB / "workspace-report-export-core.js").read_text(encoding="utf-8")

    assert 'const nativeFetch = window.fetch.bind(window);' in core
    assert 'async function buildReport(payload)' in core
    assert 'window.fetch = async function taxtreatReportAwareFetch' in core
    assert 'Tisk / PDF reportu' in core


def test_workspace_public_source_country_registry_contains_cz_and_sk():
    context = CONTEXT.read_text(encoding="utf-8")
    adapter = ADAPTER.read_text(encoding="utf-8")

    assert 'code: "CZ"' in context
    assert 'code: "SK"' in context
    assert '<option value="CZ">Česká republika</option>' in adapter
    assert '<option value="SK">Slovensko</option>' in adapter
    assert 'countryControl.hidden = true;' in adapter


def test_workspace_analysis_requests_are_bound_to_active_payer_source_country():
    adapter = ADAPTER.read_text(encoding="utf-8")

    assert 'url.includes("/analysis")' in adapter
    assert 'payload.source_country = currentCode' in adapter
    assert 'applyContext("CZ")' in adapter
    assert 'body: JSON.stringify(payload)' in adapter


def test_workspace_keeps_czech_copy_and_metrics():
    combined = ADAPTER.read_text(encoding="utf-8") + "\n" + CONTEXT.read_text(encoding="utf-8")

    assert 'Vazba ke stálé provozovně v ČR' in combined
    assert 'České subjekty, jejichž platby jsou v TaxTreat zpracovávány' in combined
    assert 'jurisdictionValue: "101"' in combined
    assert 'scopeValue: "303"' in combined


def test_workspace_browser_bundle_contains_released_slovak_copy():
    combined = ADAPTER.read_text(encoding="utf-8") + "\n" + CONTEXT.read_text(encoding="utf-8")

    assert 'Slovensko' in combined
    assert 'Slovenská zrážková daň' in combined
    assert 'OZN4311v26' in combined
    assert 'jurisdictionValue: "75"' in combined
    assert 'scopeValue: "225"' in combined
