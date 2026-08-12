from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_guided_intake_ui_is_served_without_changing_api_root():
    assert client.get("/").json() == {
        "name": "TaxTreat",
        "version": "0.2.0",
    }

    response = client.get("/ui")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert 'lang="cs"' in html
    assert 'id="case-form"' in html
    assert 'id="fx-fields"' in html
    assert 'id="questions"' in html
    assert 'id="documents"' in html
    assert 'id="calculation-card"' in html
    assert "nikoli daňové poradenství" in html


def test_guided_intake_assets_are_local_and_accessible():
    html = client.get("/ui").text
    css = client.get("/ui-assets/styles.css")
    javascript = client.get("/ui-assets/app.js")

    assert css.status_code == 200
    assert javascript.status_code == 200
    assert "/ui-assets/styles.css" in html
    assert "/ui-assets/app.js" in html
    assert "https://cdn" not in html
    assert "@media (max-width: 580px)" in css.text
    assert "--forest:" in css.text


def test_ui_calls_canonical_endpoints_and_uses_safe_dom_rendering():
    javascript = client.get("/ui-assets/app.js").text

    assert 'postJson("/analysis/intake"' in javascript
    assert 'postJson("/analysis/report"' in javascript
    assert "textContent = question.prompt" in javascript
    assert "textContent = documentName" in javascript
    assert ".innerHTML" not in javascript
    assert "exchange_rate" in javascript
    assert "payment_date" in javascript
    assert "accounting_date" in javascript


def test_ui_exposes_accessible_status_and_error_regions():
    html = client.get("/ui").text

    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    assert 'class="skip-link"' in html
    assert 'aria-label="TaxTreat domů"' in html
