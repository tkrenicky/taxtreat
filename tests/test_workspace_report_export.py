from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_workspace_loads_professional_report_export_asset():
    html = client.get("/workspace-demo").text
    asset = client.get("/ui-assets/workspace-report-export.js")

    assert asset.status_code == 200
    assert "/ui-assets/workspace-report-export.js?v=20260816-1" in html
    assert "Otevřít profesionální report" in asset.text
    assert "Tisk / uložit PDF" in asset.text
    assert 'nativeFetch("/analysis/report"' in asset.text
    assert 'url.endsWith("/analysis/intake")' in asset.text
    assert "reportWindow.print()" in asset.text
    assert "details.open = true" in asset.text


def test_workspace_output_history_is_in_memory_and_reopenable():
    asset = client.get("/ui-assets/workspace-report-export.js").text
    styles = client.get("/ui-assets/workspace-output-history.css")

    assert styles.status_code == 200
    assert "/ui-assets/workspace-output-history.css?v=20260816-2" in asset
    assert "const outputHistory = []" in asset
    assert "cacheCompletedReport" in asset
    assert "clientQuestionsRemain" in asset
    assert "Vytvořené výstupy" in asset
    assert "Poslední výstupy" in asset
    assert "dataset.outputReportId" in asset
    assert "Otevřít report" in asset
    assert "Tisk / PDF" in asset
    assert ".output-history-row" in styles.text


def test_workspace_completed_reviews_and_dashboard_metrics_are_data_bound():
    asset = client.get("/ui-assets/workspace-report-export.js").text
    styles = client.get("/ui-assets/workspace-output-history.css")

    assert "renderReviewHistory" in asset
    assert "renderDashboardMetrics" in asset
    assert "Dokončené kontroly" in asset
    assert "výsledků k odbornému ověření" in asset
    assert "dataset.reviewReportId" in asset
    assert "Otevřít výstup" in asset
    assert "statusNeedsReview" in asset
    assert ".review-history-row" in styles.text
    assert ".review-history-status" in styles.text


def test_report_export_does_not_store_transaction_payload_in_browser_storage():
    asset = client.get("/ui-assets/workspace-report-export.js").text

    assert "localStorage" not in asset
    assert "sessionStorage" not in asset
    assert "document.cookie" not in asset
    assert "lastAnalysisPayload" in asset
