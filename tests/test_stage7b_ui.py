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
    assert 'class="documents-panel"' in html
    assert 'id="calculation-card"' in html
    assert 'id="answer-error"' in html
    assert 'class="sidebar"' in html
    assert "Klientský portál" in html
    assert "Moje případy" not in html
    assert "Doklady <small>Připravujeme" not in html
    assert 'href="/docs"' not in html
    assert 'id="napoveda"' in html
    assert "Metodika a nápověda" in html
    assert "Důležité upozornění" in html
    assert "Výpočet české srážkové daně" in html
    assert "výpočet podle zadaných údajů" in html.lower()
    assert "101" in html
    assert "303" in html
    assert "Zadané údaje se po zpracování neukládají" in html
    assert "Stát plátce" in html
    assert "Stát daňové rezidence příjemce" in html
    assert "Typ příjemce" in html
    assert 'name="no_pe_connection"' in html
    assert 'id="dividend-fields"' in html
    assert 'id="advisor-review-section"' in html
    assert "Stage 6 production rules" not in html
    assert "není právním ani daňovým poradenstvím" in html
    assert "TaxTreat poskytuje strukturované právní informace" not in html
    assert "orientační" not in html.lower()
    assert "Neuzavřené právní otázky" not in html
    assert "šifrov" not in html.lower()


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
    assert "grid-template-columns: 232px" in css.text
    assert "linear-gradient(180deg, #112744" in css.text
    assert ".wizard-progress" in css.text
    assert ".wizard-navigation" in css.text
    assert ".help-section" in css.text
    assert ".help-grid" in css.text
    assert ".project-metrics" in css.text
    assert ".trust-strip" in css.text
    assert ".assumption-toggle" in css.text


def test_workspace_demo_exposes_recipient_payment_result_workflow():
    response = client.get("/workspace-demo")

    assert response.status_code == 200
    html = response.text
    assert "Návrh pracovního prostoru" in html
    assert "po obnovení se odstraní" in html
    assert "Přehled" in html
    assert "Plátci" in html
    assert "Příjemci" in html
    assert "Kontroly plateb" in html
    assert "Výstupy" in html
    assert "Komu platíš?" in html
    assert "Údaje o platbě" in html
    assert "Výsledek kontroly" in html
    assert "Proč tato sazba" in html
    assert "Další kroky" in html
    assert "Přihlášení ani ukládání klientských případů zatím není aktivní" in html
    assert "TaxTreat je výpočetní nástroj" in html
    assert "orientační" not in html.lower()


def test_workspace_demo_assets_are_local_and_use_canonical_intake():
    html = client.get("/workspace-demo").text
    css = client.get("/ui-assets/workspace.css")
    javascript = client.get("/ui-assets/workspace.js")

    assert css.status_code == 200
    assert javascript.status_code == 200
    assert "/ui-assets/workspace.css" in html
    assert "/ui-assets/workspace.js" in html
    assert 'fetch("/analysis/intake"' in javascript.text
    assert "localStorage" not in javascript.text
    assert "sessionStorage" not in javascript.text
    assert "document.cookie" not in javascript.text
    assert "textContent" in javascript.text
    assert ".innerHTML" not in javascript.text
    assert "grid-template-columns:repeat(4,1fr)" in css.text


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
    assert "Zobrazit zbývající podklady" in javascript
    assert "pageSize = 3" in javascript
    assert "wizard-progress" in javascript
    assert "Další položky" in javascript
    assert 'startsWith("facts.")' in javascript
    assert "payload.facts[factName] = answer" in javascript
    assert "Aktualizovat výpočet" in javascript
    assert "DOPLNIT ÚDAJE" in javascript
    assert "badge.textContent = statusBadgeCopy" in javascript
    assert "REVIEW_REQUIRED" in javascript
    assert 'postJson("/analysis/intake", nextPayload)' in javascript
    assert "beneficial_owner: true" in javascript
    assert "recipient_is_treaty_resident: true" in javascript
    assert "permanent_establishment_connection" in javascript
    assert "completeMonths" in javascript
    assert "renderAdvisorItems" in javascript


def test_ui_exposes_accessible_status_and_error_regions():
    html = client.get("/ui").text

    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    assert 'class="skip-link"' in html
    assert 'aria-label="TaxTreat domů"' in html
