from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"
CONTEXT = WEB / "source-country-context.js"


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


def test_workspace_sk_adapter_uses_registered_released_eur_context():
    adapter = (
        WEB / "workspace-source-country-adapter.js"
    ).read_text(encoding="utf-8")
    context = CONTEXT.read_text(encoding="utf-8")

    assert 'ctx.baseCurrency' in adapter
    assert 'if (ctx.runtimeReleased) return;' in adapter
    assert 'event.stopImmediatePropagation();' in adapter
    assert 'runtimeReleased: true' in context
    assert 'Slovenská zrážková daň v EUR' in context


def test_workspace_sk_adapter_blocks_cnb_and_hides_czech_interest_only_field():
    adapter = (
        WEB / "workspace-source-country-adapter.js"
    ).read_text(encoding="utf-8")
    context = CONTEXT.read_text(encoding="utf-8")

    combined = adapter + "\n" + context

    assert "prohibitedFxServicePrefixes" in combined
    assert "/exchange-rates/cnb" in combined
    assert "interestMonthlyAmountFieldVisible" in combined
    assert "prohibitedPrefixes" in adapter


def test_workspace_analysis_requests_are_bound_to_active_source_country():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert 'url.includes("/analysis")' in adapter
    assert 'payload.source_country = currentCode' in adapter
    assert 'body: JSON.stringify(payload)' in adapter


def test_workspace_sk_preview_replaces_remaining_czech_visible_copy_and_metrics():
    adapter = (
        WEB / "workspace-source-country-adapter.js"
    ).read_text(encoding="utf-8")
    context = CONTEXT.read_text(encoding="utf-8")

    combined = adapter + "\n" + context

    assert 'Vazba ke stálé provozovně v ČR' in combined
    assert 'Väzba príjmu na stálu prevádzkareň v SR' in combined
    assert (
        'Slovenské subjekty, ktorých platby sú v TaxTreat spracovávané'
        in combined
    )


def test_workspace_country_switch_restores_czech_copy_after_slovak_preview():
    adapter = (
        WEB / "workspace-source-country-adapter.js"
    ).read_text(encoding="utf-8")
    context = CONTEXT.read_text(encoding="utf-8")

    combined = adapter + "\n" + context

    assert 'Väzba príjmu na stálu prevádzkareň v SR' in combined
    assert 'Vazba ke stálé provozovně v ČR' in combined
    assert "applyContext" in adapter
