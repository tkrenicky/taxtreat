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
    assert 'Slovenská zrážková daň v EUR' in adapter
    assert 'ctx.complianceLegalReference' in adapter
    assert 'Mesačné oznámenie OZN4311v26' in adapter


def test_workspace_sk_adapter_blocks_cnb_and_czech_interest_only_field():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert 'url.startsWith("/exchange-rates/cnb")' in adapter
    assert 'CNB exchange-rate service is prohibited for Slovak source-country context' in adapter
    assert 'prior_same_type_monthly_amount_czk' in adapter
    assert 'interestMonthlyField.hidden = true' in adapter
    assert 'currency?.addEventListener("change", blockCnbListenerForSk, true)' in adapter
    assert 'transactionDate?.addEventListener("change", blockCnbListenerForSk, true)' in adapter


def test_workspace_analysis_requests_are_bound_to_active_source_country():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert 'url.includes("/analysis")' in adapter
    assert 'payload.source_country = currentCode' in adapter
    assert 'body: JSON.stringify(payload)' in adapter


def test_workspace_sk_preview_replaces_remaining_czech_visible_copy_and_metrics():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert 'Vazba ke stálé provozovně v ČR' in adapter
    assert 'Väzba príjmu na stálu prevádzkareň v SR' in adapter
    assert 'Slovenské subjekty, ktorých platby sú v TaxTreat spracovávané' in adapter
    assert 'České subjekty, jejichž platby jsou v TaxTreat zpracovávány.' in adapter
    assert 'jurisdictionValue.textContent = "75"' in adapter
    assert 'scopeValue.textContent = "225"' in adapter
    assert 'jurisdictionValue.textContent = "101"' in adapter
    assert 'scopeValue.textContent = "303"' in adapter


def test_workspace_country_switch_restores_czech_copy_after_slovak_preview():
    adapter = (WEB / "workspace-source-country-adapter.js").read_text(encoding="utf-8")

    assert '"Väzba príjmu na stálu prevádzkareň v SR", "Vazba ke stálé provozovně v ČR"' in adapter
    assert '"v Slovenskej republike", "v České republice"' in adapter
    assert '"v SR", "v ČR"' in adapter
    assert '"slovenského plátce", "českého plátce"' in adapter
    assert 'interestMonthlyField.hidden = false' in adapter
