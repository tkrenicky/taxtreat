from pathlib import Path

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
    assert "Přehled" in html
    assert "Plátci" in html
    assert "Příjemci" in html
    assert 'data-nav="reviews">Výsledky</button>' in html
    assert 'data-nav="outputs"' not in html
    assert "Zdroje" in html

    assert "KROK 1 ZE 4" in html
    assert "KROK 2 ZE 4" in html
    assert "KROK 3 ZE 4" in html
    assert "KROK 4 ZE 4" in html

    assert 'id="workspace-payment"' in html
    assert 'name="beneficial_owner"' in html
    assert 'name="treaty_resident"' in html
    assert 'name="pe_connection"' in html
    assert 'name="holding_period_mode"' in html
    assert 'value="known_date"' in html
    assert 'value="unknown_date"' in html
    assert 'value="at_least_12_months"' not in html
    assert 'value="less_than_12_months"' not in html

    assert "Informační nástroj:" in html
    assert "neposkytuje individuální právní ani daňové poradenství" in html.lower()


def test_guided_intake_assets_are_local_and_accessible():
    html = client.get("/ui").text
    css = client.get("/ui-assets/workspace.css?v=20260819-3")
    javascript = client.get("/ui-assets/workspace.js?v=20260819-3")
    polish = client.get("/ui-assets/workspace-client-polish.css?v=20260819-3")

    assert css.status_code == 200
    assert javascript.status_code == 200
    assert polish.status_code == 200

    assert "/ui-assets/workspace.css?v=20260819-3" in html
    assert "/ui-assets/workspace.js?v=20260819-3" in html
    assert "/ui-assets/workspace-client-polish.css?v=20260819-3" in html

    assert 'fetch("/jurisdictions"' in javascript.text
    assert "body.jurisdictions.length !== 101" in javascript.text
    assert 'fetch("/analysis/intake"' in javascript.text
    assert "localStorage" not in javascript.text
    assert "sessionStorage" not in javascript.text


def test_workspace_runtime_result_ids_are_stable_and_not_repaired_by_overlay_scripts():
    html = client.get("/workspace-demo").text
    asset = client.get("/ui-assets/workspace-report-export.js").text

    for runtime_id in (
        "workspace-tax-label",
        "workspace-tax-row-label",
        "workspace-tax",
        "workspace-rate",
        "workspace-gross",
        "workspace-tax-row",
        "workspace-net",
        "workspace-reason",
    ):
        assert f'id="{runtime_id}"' in html, runtime_id

    assert "workspace-runtime-anchor-repair" not in asset
    assert "workspace-step4-simplify-20260821.js" not in asset
    assert "workspace-step4-en-complete-20260821.js" not in asset


def test_workspace_demo_exposes_recipient_payment_result_workflow():
    response = client.get("/workspace-demo")

    assert response.status_code == 200
    html = response.text
    assert "Návrh pracovního prostoru" not in html
    assert "po obnovení se odstraní" not in html
    assert "Přehled" in html
    assert "Plátci" in html
    assert "Příjemci" in html
    assert 'data-nav="reviews">Výsledky</button>' in html
    assert 'data-nav="outputs"' not in html
    assert "Která společnost platbu provádí?" in html
    assert "Komu je placeno?" in html
    assert "Údaje o platbě" in html
    assert "<h1>Výsledek</h1>" in html
    assert "Použité právní pravidlo" in html
    assert "Podmínky použitého pravidla" in html
    assert "Odborné ověření" not in html
    assert "Rozhodné datum a navazující lhůty" in html
    assert 'id="workspace-remittance-deadline"' in html
    assert 'id="workspace-notification-deadline"' in html
    assert 'id="workspace-tax-label"' in html
    assert 'id="workspace-tax-row-label"' in html
    assert "§ 38d a § 38da zákona č. 586/1992 Sb." in html
    assert "Použité právní pravidlo" in html
    assert 'id="new-recipient-form"' in html
    assert 'id="active-payer-select"' in html
    assert 'id="payer-list"' in html
    assert 'id="flow-payer-list"' in html
    assert 'data-create-payer' in html
    assert 'name="payer_vat_id"' in html
    assert "KROK 1 ZE 4" in html
    assert "KROK 4 ZE 4" in html
    assert 'id="residency-document-form"' in html
    assert 'name="transaction_date"' in html
    assert 'name="payment_date"' not in html
    assert 'name="accounting_date"' not in html
    assert "dřívější z těchto dvou dat" in html
    assert "Výpočet vychází z níže uvedených předpokladů" in html
    assert "Pracujeme s níže uvedenými předpoklady" not in html
    assert 'id="workspace-fx-status"' in html
    assert 'name="exchange_rate_czk_per_unit"' in html
    assert "Automaticky se předvyplní kurzem ČNB" in html
    assert 'name="beneficial_owner"' in html
    assert 'name="treaty_resident"' in html
    assert 'name="pe_connection"' in html
    assert 'name="ownership_percent"' in html
    assert 'name="direct_ownership"' in html
    assert 'name="acquisition_date"' in html
    assert 'name="holding_period_mode"' in html
    assert 'value="unknown_date"' in html
    assert 'value="at_least_12_months"' not in html
    assert 'data-dividend-step="4"' in html
    assert 'id="interest-facts"' in html
    assert 'name="prior_same_type_monthly_amount_czk"' in html
    assert 'name="arm_length_amount"' in html
    assert 'data-edit-recipient' in html
    assert 'id="recipient-edit-form"' in html
    assert 'id="workspace-follow-up"' in html
    assert "4/5" not in html
    assert "Obecná knihovna" not in html
    assert "Případnou nejistotu označ" not in html
    assert "Přihlášení ani ukládání klientských případů zatím není aktivní" not in html
    assert "Informační nástroj:" in html
    assert "neposkytuje individuální právní ani daňové poradenství" in html.lower()
    assert "Právní dataset:" not in html
    assert "orientační" not in html.lower()


def test_design_lab_exposes_three_distinct_functional_directions():
    response = client.get("/design-lab")

    assert response.status_code == 200
    html = response.text
    assert "01 · HALO" in html
    assert "02 · APERTURE" in html
    assert "03 · SIGNAL" in html
    assert "/design-lab/editorial" in html
    assert "/design-lab/atlas" in html
    assert "/design-lab/civic" in html
    assert "Stejný produkt" in html
    assert client.get("/ui-assets/design-lab.css").status_code == 200
    assert client.get("/ui-assets/design-lab-v2.css").status_code == 200
    for design in ("editorial", "atlas", "civic"):
        variant = client.get(f"/design-lab/{design}")
        assert variant.status_code == 200
        assert variant.headers["cache-control"] == "no-store"
    assert client.get("/design-lab/unknown").status_code == 404


def test_browser_acceptance_uses_current_result_status_wording():
    source = (
        Path("scripts/capture_stage7b_ui.py")
        .read_text(encoding="utf-8")
    )

    assert "workspace-result-status" in source
    assert "VÝSLEDEK DOKONČEN" not in source


def test_workspace_demo_assets_are_local_and_use_canonical_intake():
    html = client.get("/workspace-demo").text
    css = client.get("/ui-assets/workspace.css")
    javascript = client.get("/ui-assets/workspace.js")
    designs = client.get("/ui-assets/workspace-designs.css")

    assert css.status_code == 200
    assert javascript.status_code == 200
    assert designs.status_code == 200
    assert "/ui-assets/workspace.css?v=20260819-3" in html
    assert "/ui-assets/workspace.js?v=20260819-3" in html
    assert "/ui-assets/workspace-designs.css?v=20260819-3" in html
    assert 'id="design-switcher"' not in html
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
    assert "Upravit plátce" in javascript.text
    assert "Upravit příjemce" in html
    assert "payer-choice-edit" in javascript.text
    assert "data-tooltip" in javascript.text
    assert "renderTransactionFacts" in javascript.text
    assert "updateDividendProgress" in javascript.text
    assert "decisiveCitations" in javascript.text
    assert "citationRole" in javascript.text
    assert 'domestic: 0, treaty: 1' in javascript.text
    assert "index + 1" in javascript.text
    assert "1. Výchozí vnitrostátní pravidlo" not in javascript.text
    assert "concreteReviewItems" in javascript.text
    assert "review_reasons" in javascript.text
    assert "Konkrétní důvod je uveden" in javascript.text
    assert "selectedCitation" in javascript.text
    assert "citation.excerpt" in javascript.text
    assert "citation.conditions" in javascript.text
    assert "citation.legal_layer" in javascript.text
    assert "CURRENT-1" not in javascript.text
    assert "CURRENT-2" not in javascript.text
    assert "/sm/2007/31/" not in javascript.text
    assert "Článek 10 odst." not in javascript.text
    assert "build_withholding_compliance_schedule" not in javascript.text
    assert "renderComplianceSchedule" in javascript.text
    assert "exclusive_foreign_taxation" in javascript.text
    assert "domestic_exemption" in javascript.text
    assert "Česká daň k odvodu" in javascript.text
    assert "Při 0% výsledku" not in javascript.text
    assert "Smluvní pravidlo přiznává právo zdanit příjem pouze" in javascript.text
    assert "withholding_compliance_schedule" in javascript.text
    assert "citation.source_id" not in javascript.text
    assert "evidovaný zdroj" not in javascript.text
    assert 'incomeType === "royalty"' in javascript.text
    assert 'incomeType === "interest"' in javascript.text
    assert 'data.get("transaction_date")' in javascript.text
    assert "facts.ownership_percent" in javascript.text
    assert "recipientEditForm.addEventListener" in javascript.text
    assert "let payers = [" in javascript.text
    assert "activePayerKey" in javascript.text
    assert "currentRelationship" in javascript.text
    assert "renderPayers" in javascript.text
    assert "recipient.relationships" in javascript.text
    assert "Právní dataset:" not in javascript.text
    assert 'fetch(`/exchange-rates/cnb?' in javascript.text
    assert "syncExchangeRateFromField" in javascript.text
    assert "ručně upraven" in javascript.text
    assert "Znění použitého ustanovení" in javascript.text
    assert "Evidované znění použitého ustanovení" in javascript.text
    assert "Znění použitého ustanovení" in javascript.text
    assert "analysis.legal_path" in javascript.text
    assert "excerptHasBrokenEncoding" in javascript.text
    assert "Zobrazit schválený text ustanovení" not in javascript.text
    assert "displayLegalExcerpt" in javascript.text
    assert "excerptIsReadable" not in javascript.text
    assert "Odkaz na kurzovní lístek ČNB" not in javascript.text
    assert 'document.body.dataset.design = design' in javascript.text
    assert "routeDesign" in javascript.text
    assert "countryNames" not in javascript.text
    assert "countryName(recipient.country)" in javascript.text
    assert 'body[data-design="editorial"]' in designs.text
    assert 'body[data-design="atlas"]' in designs.text
    assert 'body[data-design="civic"]' in designs.text
    assert "01 — Halo" in designs.text
    assert "02 — Aperture" in designs.text
    assert "03 — Signal" in designs.text
    assert "border-radius:26px" in designs.text
    assert "non_taxing_interest_above_monthly_threshold_annual" in javascript.text
    assert "non_taxing_interest_monthly_threshold_not_exceeded" in javascript.text
    assert "§ 38da zákona č. 586/1992 Sb." in javascript.text
    assert 'const BUILD_VERSION = "20260819-3"' in javascript.text
    assert "Načíst novou verzi" in javascript.text
    assert ".new-build-notice" in css.text
    assert ".dashboard-summary" in css.text
    assert 'class="payment-currency-field"' in html
    assert 'id="workspace-exchange-rate-field"' in html
    assert "grid-template-columns: repeat(6, 1fr)" in css.text
    assert (
        ".payment-currency-field,\n#workspace-exchange-rate-field"
        in css.text
    )
    assert ".dashboard-metrics" in css.text
    assert ".fx-status.success" in css.text
    assert "grid-template-columns:repeat(4,1fr)" in css.text
    assert ".profile-form-grid" in css.text
    assert ".question-card" in css.text
    assert ".progressive-facts" in css.text
    assert ".fact-question" in css.text
    assert ".modal::backdrop" in css.text
    assert ".compliance-schedule" in css.text
    assert ".citation-card blockquote" in css.text
    assert ".citation-excerpt" in css.text
    assert "font-size: .88rem" in css.text


def test_real_cz_at_result_returns_domestic_then_treaty_legal_path():
    response = client.post(
        "/analysis/intake",
        json={
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
            "transaction_date": "2026-08-12",
            "facts": {
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
                "permanent_establishment_connection": False,
                "recipient_entity_type": "company",
                "ownership_percent": 11,
                "direct_ownership": True,
                "direct_or_indirect_voting_ownership": 11,
                "holding_period_months": 0,
            },
            "determinations": {},
            "transaction_amount": {
                "amount": "100000",
                "currency": "CZK",
                "payment_date": "2026-08-12",
                "accounting_date": "2026-08-12",
            },
        },
    )

    assert response.status_code == 200
    legal_path = response.json()["analysis"]["legal_path"]
    assert [(item["legal_layer"], item["rate"]) for item in legal_path] == [
        ("domestic", 15.0),
        ("treaty", 0.0),
    ]
    assert "Dividendy vyplácené společností" in legal_path[1][
        "official_text"
    ]
    assert "spolecnostõ" not in legal_path[1]["official_text"]
    assert legal_path[1]["source_url"].startswith("https://e-sbirka.gov.cz/")


def test_cz_at_result_before_catalog_source_version_keeps_domestic_start():
    response = client.post(
        "/analysis/intake",
        json={
            "source_country": "CZ",
            "recipient_country": "AT",
            "income_type": "dividend",
            "transaction_date": "2026-03-01",
            "facts": {
                "beneficial_owner": True,
                "recipient_is_treaty_resident": True,
                "permanent_establishment_connection": False,
                "recipient_entity_type": "company",
                "ownership_percent": 9,
                "direct_ownership": True,
                "direct_or_indirect_voting_ownership": 9,
                "holding_period_months": 0,
            },
            "determinations": {},
            "transaction_amount": {
                "amount": "100000",
                "currency": "CZK",
                "payment_date": "2026-03-01",
                "accounting_date": "2026-03-01",
            },
        },
    )

    assert response.status_code == 200
    legal_path = response.json()["analysis"]["legal_path"]
    assert [(item["legal_layer"], item["rate"]) for item in legal_path] == [
        ("domestic", 15.0),
        ("treaty", 10.0),
    ]
    assert legal_path[0]["path_role"] == "domestic_starting_point"


def test_ui_calls_canonical_endpoints_and_uses_safe_dom_rendering():
    javascript = client.get("/ui-assets/workspace.js?v=20260819-3").text
    html = client.get("/ui").text

    assert 'fetch("/analysis/intake"' in javascript
    assert "textContent" in javascript
    assert ".innerHTML" not in javascript
    assert "exchange_rate" in javascript
    assert "transaction_date" in javascript
    assert "withholding_compliance_schedule" in javascript
    assert 'id="workspace-tax-label"' in html
    assert 'id="workspace-result-status"' in html
    assert 'id="workspace-citations"' in html
    assert 'id="workspace-notification-deadline"' in html


def test_ui_exposes_accessible_status_and_error_regions():
    html = client.get("/ui").text

    assert 'aria-live="polite"' in html
    assert 'role="alert"' in html
    assert 'aria-label="Hlavní navigace"' in html
    assert 'aria-label="Průběh kontroly"' in html


def test_ui_does_not_render_raw_eu_relief_structured_excerpt():
    javascript = client.get("/ui-assets/workspace.js?v=20260819-3").text

    assert 'const canShowRawExcerpt = ["treaty", "protocol", "mli"].includes(layer);' in javascript
    assert '|| (canShowRawExcerpt && Boolean(citation.excerpt));' in javascript
    assert '(layer !== "domestic" || hasDomesticDisclosure)' not in javascript


def test_step4_english_exact_translation_is_case_insensitive_for_section19():
    javascript = client.get("/ui-assets/workspace-step4-en-complete-20260821.js").text

    assert 'toLocaleLowerCase("cs-CZ")' in javascript
    assert '["Vnitrostátní osvobození podle § 19 ZDP", "Domestic exemption under Section 19"]' in javascript
    assert '["§ 19 ZDP se použije", "Section 19 applies"]' in javascript


def test_english_treaty_locale_provenance_statuses_are_public_and_badged():
    javascript = client.get("/ui-assets/workspace-treaty-excerpt-locales-20260824.js").text

    for status in (
        "official_translation_non_authentic",
        "official_synthesised_text",
        "official_synthesised_excerpt",
        "machine_translation_from_official_text",
        "current_application_suspended",
    ):
        assert f'"{status}"' in javascript

    assert "Official English translation — non-authentic" in javascript
    assert "Official-source synthesised English text" in javascript
    assert "Machine translation of official text" in javascript
    assert "Application currently suspended" in javascript
    assert "renderStatusNotice(card, locale);" in javascript
