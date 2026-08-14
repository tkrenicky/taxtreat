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
    assert "Jak výsledek číst" in html
    assert "Odborné ověření" in html
    assert "Rozhodné datum a navazující lhůty" in html
    assert 'id="workspace-remittance-deadline"' in html
    assert 'id="workspace-notification-deadline"' in html
    assert "§ 38d / § 38da" in html
    assert "Jak výsledek číst" in html
    assert 'id="new-recipient-form"' in html
    assert 'data-edit-payer' in html
    assert 'id="residency-document-form"' in html
    assert 'name="transaction_date"' in html
    assert 'name="payment_date"' not in html
    assert 'name="accounting_date"' not in html
    assert "dřívější z těchto dvou dat" in html
    assert 'name="beneficial_owner"' in html
    assert 'name="treaty_resident"' in html
    assert 'name="pe_connection"' in html
    assert 'name="ownership_percent"' in html
    assert 'name="direct_ownership"' in html
    assert 'name="acquisition_date"' in html
    assert 'name="holding_period_mode"' in html
    assert 'value="at_least_12_months"' in html
    assert 'data-dividend-step="4"' in html
    assert 'id="interest-facts"' in html
    assert 'name="arm_length_amount"' in html
    assert 'data-edit-recipient' in html
    assert 'id="recipient-edit-form"' in html
    assert 'id="workspace-follow-up"' in html
    assert "4/5" not in html
    assert "Obecná knihovna" not in html
    assert "Případnou nejistotu označ" not in html
    assert "Přihlášení ani ukládání klientských případů zatím není aktivní" in html
    assert "TaxTreat je výpočetní nástroj" in html
    assert "nepředstavuje právní ani daňové poradenství" in html
    assert "Právní dataset:" not in html
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
    assert "resultExplanation" in javascript.text
    assert "citationCard" in javascript.text
    assert "Byla identifikována sazba" in javascript.text
    assert "Otevřít zdroj" in javascript.text
    assert "recipientForm.addEventListener" in javascript.text
    assert "renderClientQuestions" in javascript.text
    assert "applyAnswers" in javascript.text
    assert "clientAnswers" in javascript.text
    assert "showModal" in javascript.text
    assert "data-tooltip" in javascript.text
    assert "renderTransactionFacts" in javascript.text
    assert "updateDividendProgress" in javascript.text
    assert "decisiveCitations" in javascript.text
    assert "concreteReviewItems" in javascript.text
    assert "Vazba podílu ke stálé provozovně" in javascript.text
    assert "citationExcerpt" in javascript.text
    assert "Dvanáctiměsíční doba držby" not in javascript.text
    assert "dvanáctiměsíční doba držby" in javascript.text
    assert "build_withholding_compliance_schedule" not in javascript.text
    assert "renderComplianceSchedule" in javascript.text
    assert "withholding_compliance_schedule" in javascript.text
    assert "citation.source_id" not in javascript.text
    assert "evidovaný zdroj" not in javascript.text
    assert 'incomeType === "royalty"' in javascript.text
    assert 'incomeType === "interest"' in javascript.text
    assert 'data.get("transaction_date")' in javascript.text
    assert "facts.ownership_percent" in javascript.text
    assert "recipientEditForm.addEventListener" in javascript.text
    assert "Právní dataset:" not in javascript.text
    assert "grid-template-columns:repeat(4,1fr)" in css.text
    assert ".profile-form-grid" in css.text
    assert ".question-card" in css.text
    assert ".progressive-facts" in css.text
    assert ".fact-question" in css.text
    assert ".modal::backdrop" in css.text
    assert ".compliance-schedule" in css.text
    assert ".citation-card blockquote" in css.text


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
