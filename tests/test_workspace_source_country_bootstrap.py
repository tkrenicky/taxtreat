from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_workspace_bootstrap_loads_country_context_and_adapter_before_existing_export_core():
    bootstrap = (WEB / "workspace-report-export.js").read_text(encoding="utf-8")

    country = '/ui-assets/source-country-context.js?v=20260819-sk1'
    adapter = '/ui-assets/workspace-source-country-adapter.js?v=20260819-sk1'
    core = '/ui-assets/workspace-report-export-core.js?v=20260819-3'

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


def test_workspace_sk_adapter_is_prerelease_fail_closed_and_uses_eur_context():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert 'Slovensko · před vydáním' in adapter
    assert 'ctx.baseCurrency' in adapter
    assert 'if (ctx.runtimeReleased) return;' in adapter
    assert 'event.stopImmediatePropagation();' in adapter
    assert 'Slovenská zrážková daň' in adapter
    assert 'ctx.complianceLegalReference' in adapter
