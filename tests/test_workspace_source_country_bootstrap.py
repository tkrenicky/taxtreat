from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_workspace_bootstrap_loads_country_context_before_existing_export_core():
    bootstrap = (WEB / "workspace-report-export.js").read_text(encoding="utf-8")

    country = '/ui-assets/source-country-context.js?v=20260819-sk1'
    core = '/ui-assets/workspace-report-export-core.js?v=20260819-3'

    assert country in bootstrap
    assert core in bootstrap
    assert bootstrap.index(country) < bootstrap.index(core)


def test_workspace_existing_report_export_logic_is_preserved_as_core():
    core = (WEB / "workspace-report-export-core.js").read_text(encoding="utf-8")

    assert 'const nativeFetch = window.fetch.bind(window);' in core
    assert 'async function buildReport(payload)' in core
    assert 'window.fetch = async function taxtreatReportAwareFetch' in core
    assert 'Tisk / PDF reportu' in core
