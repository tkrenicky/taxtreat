from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _report_export_bundle_text():
    bootstrap = client.get(
        "/ui-assets/workspace-report-export.js"
    ).text
    core = client.get(
        "/ui-assets/workspace-report-export-core.js?v=20260819-3"
    )

    assert core.status_code == 200
    return bootstrap + "\n" + core.text


def test_workspace_loads_pdf_report_export_asset():
    html = client.get("/workspace-demo").text
    asset = client.get("/ui-assets/workspace-report-export.js")

    assert asset.status_code == 200
    assert "/ui-assets/workspace-report-export.js?v=20260819-3" in html
    assert "Tisk / PDF reportu" in html
    bundle = _report_export_bundle_text()
    assert "Tisk / PDF reportu" in bundle
    assert 'nativeFetch("/analysis/report"' in bundle
    assert 'url.endsWith("/analysis/intake")' in bundle
    assert "reportWindow.print()" in bundle
    assert "details.open = true" in bundle


def test_workspace_output_history_is_in_memory_and_printable():
    asset = _report_export_bundle_text()
    styles = client.get("/ui-assets/workspace-output-history.css")

    assert styles.status_code == 200
    assert "/ui-assets/workspace-output-history.css?v=20260819-3" in asset
    assert "const outputHistory = []" in asset
    assert "cacheCompletedReport" in asset
    assert "openStoredResult" in asset
    assert "clientQuestionsRemain" in asset
    assert "Otevřít výsledek" in asset
    assert "Poslední výsledky" in asset
    assert "dataset.outputReportId" in asset
    assert "Tisk / PDF" in asset
    assert ".output-history-row" in styles.text


def test_workspace_completed_reviews_and_dashboard_metrics_are_data_bound():
    asset = _report_export_bundle_text()
    styles = client.get("/ui-assets/workspace-output-history.css")

    assert "renderReviewHistory" in asset
    assert "renderDashboardMetrics" in asset
    assert "Dokončené výpočty" in asset
    assert "výpočtů s chybějícími údaji" in asset
    assert "dataset.reviewReportId" in asset
    assert "Tisk / PDF" in asset
    assert "statusNeedsReview" in asset
    assert ".review-history-row" in styles.text
    assert ".review-history-status" in styles.text


def test_report_export_does_not_store_transaction_payload_in_browser_storage():
    asset = _report_export_bundle_text()

    assert "localStorage" not in asset
    assert "sessionStorage" not in asset
    assert "document.cookie" not in asset
    assert "lastAnalysisPayload" in asset
