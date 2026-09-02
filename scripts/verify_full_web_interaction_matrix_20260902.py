from __future__ import annotations

import json
import subprocess
import sys
import time
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "full_web_interaction_matrix_20260902.json"
BASE_URL = "http://127.0.0.1:8765"

ROYALTY_CATEGORIES = [
    "copyright_literary_artistic_scientific_nonfilm_nonsoftware",
    "cinematographic_films_or_broadcast_media",
    "computer_software",
    "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    "financial_lease_of_equipment",
    "operating_lease_or_other_use_of_equipment",
    "other",
]

SPECIAL_BOOLEAN_FACTS = [
    "article_10_public_body_exemption",
    "article_11_public_body_exemption",
    "recipient_is_bank",
    "recipient_is_financial_institution_or_insurer",
    "recipient_has_share_capital",
    "article_11_3_public_financing_exemption",
    "recipient_is_qualifying_pension_fund",
    "recipient_is_central_bank",
    "article_10_3_public_body_exemption",
]


def base_payload(country: str, income: str) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "beneficial_owner": True,
        "recipient_is_treaty_resident": True,
        "permanent_establishment_connection": False,
        "recipient_entity_type": "company",
        "ownership_percent": 25.0,
        "direct_ownership": True,
        "direct_or_indirect_voting_ownership": 25.0,
        "holding_period_months": 24,
        "arm_length_amount": True,
        "payment_is_arm_length_amount": True,
        "prior_same_type_monthly_amount_czk": 0,
        "royalty_category": "patent_trademark_design_model_plan_secret_formula_process_or_knowhow",
    }
    for fact in SPECIAL_BOOLEAN_FACTS:
        facts[fact] = False
    return {
        "source_country": "CZ",
        "recipient_country": country,
        "income_type": income,
        "transaction_date": "2026-08-12",
        "facts": facts,
        "determinations": {},
        "transaction_amount": {
            "amount": "100000",
            "currency": "CZK",
            "payment_date": "2026-08-12",
            "accounting_date": "2026-08-12",
        },
    }


def variants(country: str, income: str) -> list[tuple[str, dict[str, Any]]]:
    base = base_payload(country, income)
    result: list[tuple[str, dict[str, Any]]] = [("baseline", deepcopy(base))]

    for name, fact, value in [
        ("beneficial_owner_false", "beneficial_owner", False),
        ("treaty_resident_false", "recipient_is_treaty_resident", False),
        ("pe_connection_true", "permanent_establishment_connection", True),
    ]:
        payload = deepcopy(base)
        payload["facts"][fact] = value
        result.append((name, payload))

    if income == "dividend":
        for value in [0, 4.99, 5, 9.99, 10, 24.99, 25, 49.99, 50, 100]:
            payload = deepcopy(base)
            payload["facts"]["ownership_percent"] = value
            payload["facts"]["direct_or_indirect_voting_ownership"] = value
            result.append((f"ownership_{value}", payload))
        payload = deepcopy(base)
        payload["facts"]["direct_ownership"] = False
        result.append(("indirect_ownership", payload))
        for months in [0, 11, 12, 23, 24, 36]:
            payload = deepcopy(base)
            payload["facts"]["holding_period_months"] = months
            result.append((f"holding_{months}_months", payload))
        for value in [0, 10, 25, 50, 100]:
            payload = deepcopy(base)
            payload["facts"]["direct_or_indirect_voting_ownership"] = value
            result.append((f"voting_{value}", payload))
        for fact in [
            "article_10_public_body_exemption",
            "recipient_is_qualifying_pension_fund",
            "recipient_is_central_bank",
            "article_10_3_public_body_exemption",
            "recipient_has_share_capital",
        ]:
            payload = deepcopy(base)
            payload["facts"][fact] = True
            result.append((f"{fact}_true", payload))

    if income == "interest":
        payload = deepcopy(base)
        payload["facts"]["arm_length_amount"] = False
        payload["facts"]["payment_is_arm_length_amount"] = False
        result.append(("not_arm_length", payload))
        for amount in [0, 9999, 100000, 1000000]:
            payload = deepcopy(base)
            payload["facts"]["prior_same_type_monthly_amount_czk"] = amount
            result.append((f"prior_monthly_{amount}", payload))
        for fact in [
            "article_11_public_body_exemption",
            "recipient_is_bank",
            "recipient_is_financial_institution_or_insurer",
            "article_11_3_public_financing_exemption",
        ]:
            payload = deepcopy(base)
            payload["facts"][fact] = True
            result.append((f"{fact}_true", payload))

    if income == "royalty":
        for category in ROYALTY_CATEGORIES:
            payload = deepcopy(base)
            payload["facts"]["royalty_category"] = category
            result.append((f"royalty_{category}", payload))

    return result


def wait_for_server() -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/", timeout=1.0)
            if response.status_code == 200:
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("Local web server did not become ready")


def run_api_matrix(report: dict[str, Any]) -> None:
    client = httpx.Client(base_url=BASE_URL, timeout=20.0)
    jurisdictions_response = client.get("/jurisdictions")
    jurisdictions_response.raise_for_status()
    jurisdictions = jurisdictions_response.json()["jurisdictions"]
    countries = sorted(str(item["iso2"]).upper() for item in jurisdictions)
    report["api"]["jurisdiction_count"] = len(countries)
    report["api"]["jurisdictions"] = countries

    if len(countries) != 101:
        report["blockers"].append(f"/jurisdictions returned {len(countries)} countries instead of 101")

    requests_total = 0
    status_counts: dict[str, int] = {}
    hard_failures: list[dict[str, Any]] = []
    report_status_counts: dict[str, int] = {}
    report_failures: list[dict[str, Any]] = []
    baseline_statuses: dict[str, int] = {}
    analysis_statuses: dict[str, int] = {}
    finalizable_scopes: set[str] = set()

    for country in countries:
        for income in ("dividend", "interest", "royalty"):
            scope = f"{country}:{income}"
            baseline_payload = None
            baseline_body = None
            for variant_name, payload in variants(country, income):
                requests_total += 1
                try:
                    response = client.post("/analysis/intake", json=payload)
                    status_counts[str(response.status_code)] = status_counts.get(str(response.status_code), 0) + 1
                    try:
                        body = response.json()
                    except Exception:
                        body = None
                    if variant_name == "baseline":
                        baseline_statuses[scope] = response.status_code
                        baseline_payload = payload
                        baseline_body = body
                    if response.status_code >= 500 or body is None:
                        hard_failures.append({
                            "scope": scope,
                            "variant": variant_name,
                            "status": response.status_code,
                            "body": response.text[:1000],
                        })
                        continue
                    if response.status_code != 200:
                        hard_failures.append({
                            "scope": scope,
                            "variant": variant_name,
                            "status": response.status_code,
                            "body": body,
                        })
                        continue
                    analysis = body.get("analysis") if isinstance(body, dict) else None
                    if isinstance(analysis, dict):
                        astatus = str(analysis.get("status") or "UNKNOWN")
                        analysis_statuses[astatus] = analysis_statuses.get(astatus, 0) + 1
                        if astatus == "FINAL":
                            finalizable_scopes.add(scope)
                except Exception as exc:
                    hard_failures.append({
                        "scope": scope,
                        "variant": variant_name,
                        "exception": repr(exc),
                    })

            if baseline_payload is not None:
                try:
                    response = client.post("/analysis/report", json=baseline_payload)
                    report_status_counts[str(response.status_code)] = report_status_counts.get(str(response.status_code), 0) + 1
                    try:
                        body = response.json()
                    except Exception:
                        body = None
                    if response.status_code == 200:
                        if not isinstance(body, dict) or not body.get("html") or not body.get("report"):
                            report_failures.append({
                                "scope": scope,
                                "status": response.status_code,
                                "reason": "200 response missing html/report",
                            })
                    elif response.status_code >= 500:
                        report_failures.append({
                            "scope": scope,
                            "status": response.status_code,
                            "body": response.text[:1000],
                        })
                    else:
                        detail = body.get("detail") if isinstance(body, dict) else None
                        report_failures.append({
                            "scope": scope,
                            "status": response.status_code,
                            "detail": detail,
                            "baseline_analysis_status": (
                                baseline_body.get("analysis", {}).get("status")
                                if isinstance(baseline_body, dict)
                                else None
                            ),
                        })
                except Exception as exc:
                    report_failures.append({"scope": scope, "exception": repr(exc)})

    report["api"].update({
        "matrix_request_count": requests_total,
        "status_counts": status_counts,
        "analysis_status_counts": analysis_statuses,
        "baseline_scope_count": len(baseline_statuses),
        "baseline_non_200": {
            key: value for key, value in baseline_statuses.items() if value != 200
        },
        "finalizable_scope_count_across_variants": len(finalizable_scopes),
        "hard_failure_count": len(hard_failures),
        "hard_failures": hard_failures[:200],
        "report_status_counts": report_status_counts,
        "report_failure_count": len(report_failures),
        "report_failures": report_failures[:303],
    })
    if hard_failures:
        report["blockers"].append(f"API matrix has {len(hard_failures)} non-200/invalid responses")
    if any(item.get("status", 0) >= 500 for item in report_failures):
        report["blockers"].append("At least one report request returned a server error")


def visible(locator) -> bool:
    try:
        return locator.is_visible()
    except Exception:
        return False


def run_browser_audit(report: dict[str, Any]) -> None:
    browser_report: dict[str, Any] = report["browser"]
    page_errors: list[str] = []
    console_errors: list[str] = []
    tested: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/workspace-demo", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector("#workspace-payment", state="attached", timeout=10000)
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_selector("#workspace-payment", state="attached", timeout=10000)

        # Jurisdiction catalog must expand both recipient selects to all 101.
        page.wait_for_function(
            "() => document.querySelector('#new-recipient-form select[name=recipient_country]')?.options.length >= 101",
            timeout=10000,
        )
        new_country_select = page.locator("#new-recipient-form select[name=recipient_country]")
        edit_country_select = page.locator("#recipient-edit-form select[name=recipient_country]")
        new_options = new_country_select.locator("option").evaluate_all(
            "(els) => els.map(e => ({value:e.value,text:e.textContent}))"
        )
        edit_options = edit_country_select.locator("option").evaluate_all(
            "(els) => els.map(e => ({value:e.value,text:e.textContent}))"
        )
        browser_report["new_recipient_country_option_count"] = len([x for x in new_options if x["value"]])
        browser_report["edit_recipient_country_option_count"] = len([x for x in edit_options if x["value"]])
        if browser_report["new_recipient_country_option_count"] != 101:
            report["blockers"].append("New-recipient UI does not expose all 101 recipient countries after JS load")
        if browser_report["edit_recipient_country_option_count"] != 101:
            report["blockers"].append("Recipient-edit UI does not expose all 101 recipient countries after JS load")

        # Cycle every recipient country option and every recipient type.
        for option in [x["value"] for x in new_options if x["value"]]:
            new_country_select.select_option(option, force=True)
        tested.append("all_101_new_recipient_country_options")
        for option in [x["value"] for x in edit_options if x["value"]]:
            edit_country_select.select_option(option, force=True)
        tested.append("all_101_edit_recipient_country_options")

        page.locator("[data-create-recipient]").first.click()
        page.wait_for_selector("#new-recipient-form:not([hidden])")
        recipient_types = page.locator("#new-recipient-form select[name=recipient_type] option").all_text_contents()
        for label in recipient_types:
            page.locator("#new-recipient-form select[name=recipient_type]").select_option(label=label)
        tested.append("all_recipient_types")
        page.locator("[data-next-step='1']").click()

        # Public source-country contract.
        public_source_countries = page.evaluate(
            "() => Object.keys(window.TaxTreatSourceCountries?.countries || {})"
        )
        browser_report["public_source_countries"] = public_source_countries
        if "SK" not in public_source_countries:
            report["blockers"].append(
                "Public workspace source-country context exposes CZ only; released SK is not selectable"
            )

        # Main navigation buttons.
        for nav in ["dashboard", "payers", "recipients", "reviews", "sources"]:
            page.locator(f"[data-nav='{nav}']").first.click()
            page.wait_for_timeout(80)
            if not page.locator(f"[data-view='{nav}']").is_visible():
                report["blockers"].append(f"Navigation button {nav} did not show its view")
        tested.append("all_main_navigation")

        # Language control must switch both directions and survive navigation.
        lang_buttons = page.locator("#taxtreat-language-controls button[data-lang]")
        browser_report["language_button_count"] = lang_buttons.count()
        if lang_buttons.count() < 2:
            report["blockers"].append("CZ/EN language controls are not both present")
        else:
            page.locator("#taxtreat-language-controls button[data-lang='en']").click()
            page.wait_for_timeout(700)
            if page.evaluate("document.documentElement.lang") != "en":
                report["blockers"].append("EN language switch did not set document language to en")
            if "Information tool:" not in page.locator(".information-only-note").inner_text():
                report["blockers"].append("EN language switch did not translate information notice")
            page.locator("[data-nav='payers']").first.click()
            page.wait_for_timeout(250)
            if page.evaluate("localStorage.getItem('taxtreat-ui-language')") != "en":
                report["blockers"].append("EN language setting did not persist across navigation")
            page.locator("#taxtreat-language-controls button[data-lang='cs']").click()
            page.wait_for_timeout(700)
            if page.evaluate("document.documentElement.lang") != "cs":
                report["blockers"].append("CZ language switch did not restore document language to cs")
            tested.append("language_cs_en_roundtrip")

        # Payer dialog: invalid ARES validation, manual save, active payer switching, edit.
        page.locator("[data-create-payer]").first.click()
        page.wait_for_selector("#payer-dialog[open]")
        page.locator("#payer-form input[name=payer_id]").fill("123")
        page.locator("[data-ares-lookup]").click()
        page.wait_for_timeout(150)
        if "8 číslic" not in page.locator("#ares-lookup-status").inner_text():
            report["blockers"].append("ARES invalid-IČO validation did not fire")
        page.locator("#payer-form input[name=payer_id]").fill("11111111")
        page.locator("#payer-form input[name=payer_name]").fill("Audit Payer s.r.o.")
        page.locator("#payer-form input[name=payer_vat_id]").fill("CZ11111111")
        page.locator("[data-save-payer]").click()
        page.wait_for_timeout(300)
        if page.locator("#active-payer-select option").count() < 3:
            report["blockers"].append("Adding a payer did not add it to active payer selector")
        page.locator("[data-nav='payers']").first.click()
        edit_buttons = page.locator("#payer-list button", has_text="Upravit")
        if edit_buttons.count():
            edit_buttons.last.click()
            page.wait_for_selector("#payer-dialog[open]")
            page.locator("#payer-form input[name=payer_name]").fill("Audit Payer Edited s.r.o.")
            page.locator("[data-save-payer]").click()
            page.wait_for_timeout(250)
        tested.append("payer_add_edit_invalid_ares")

        # Recipient edit dialog and every select option.
        page.locator("[data-nav='recipients']").first.click()
        page.locator("[data-edit-recipient]").first.click()
        page.wait_for_selector("#recipient-dialog[open]")
        for name in ["recipient_type", "direct_ownership", "beneficial_owner", "treaty_resident", "pe_connection"]:
            select = page.locator(f"#recipient-edit-form select[name='{name}']")
            values = select.locator("option").evaluate_all("(els) => els.map(e => e.value)")
            for value in values:
                select.select_option(value)
        page.locator("#recipient-edit-form select[name=recipient_country]").select_option("AT")
        page.locator("#recipient-edit-form input[name=recipient_name]").fill("Audit GmbH")
        page.locator("#recipient-edit-form button[type=submit]").click()
        page.wait_for_timeout(250)
        tested.append("recipient_edit_all_select_options")

        # Residency evidence open/cancel/save.
        page.locator("[data-open-recipient]").first.click()
        page.locator("[data-residency-document]").click()
        if not page.locator("#residency-document-form").is_visible():
            report["blockers"].append("Residency-document button did not open form")
        page.locator("[data-close-residency]").click()
        page.locator("[data-residency-document]").click()
        page.locator("#residency-document-form input[name=issued_at]").fill("2026-01-01")
        page.locator("#residency-document-form input[name=valid_until]").fill("2026-12-31")
        page.locator("#residency-document-form button[type=submit]").click()
        page.wait_for_timeout(150)
        tested.append("residency_document_open_cancel_save")

        # Flow navigation forward/backward and progress buttons.
        page.locator("[data-start-flow]").first.click()
        for step in [2, 1, 2, 3, 2, 3]:
            page.locator(f"[data-next-step='{step}']").first.click()
            page.wait_for_timeout(80)
            active = page.locator(f".flow-step[data-step='{step}']")
            if not active.is_visible():
                report["blockers"].append(f"Flow navigation failed to show step {step}")
        tested.append("flow_forward_backward")

        form = page.locator("#workspace-payment")
        # Common assumption radios: every value.
        for name in ["beneficial_owner", "treaty_resident", "pe_connection"]:
            for value in ["true", "false"]:
                form.locator(f"input[name='{name}'][value='{value}']").check()
        form.locator("input[name=beneficial_owner][value=true]").check()
        form.locator("input[name=treaty_resident][value=true]").check()
        form.locator("input[name=pe_connection][value=false]").check()
        tested.append("all_common_boolean_inputs")

        # Currency/FX combinations.
        for currency in ["CZK", "EUR", "USD", "CHF", "GBP"]:
            form.locator("select[name=currency]").select_option(currency)
            page.wait_for_timeout(250)
            fx_field = page.locator("#workspace-exchange-rate-field")
            if currency == "CZK":
                if fx_field.is_visible():
                    report["blockers"].append("FX field is visible for CZK")
            else:
                # Automatic CNB fetch may be unavailable in CI. UI must at least expose manual input.
                if not fx_field.is_visible():
                    report["blockers"].append(f"FX field did not become visible for {currency}")
                else:
                    form.locator("input[name=exchange_rate_czk_per_unit]").fill("25")
        form.locator("select[name=currency]").select_option("CZK")
        tested.append("all_currency_options_and_fx_visibility")

        # Tooltips.
        for button in page.locator("[data-tooltip]").all():
            try:
                button.click()
                page.wait_for_timeout(40)
            except Exception:
                pass
        tested.append("all_tooltip_buttons")

        # Income-specific controls and boundary values.
        form.locator("select[name=income_type]").select_option("dividend")
        page.wait_for_timeout(100)
        if not page.locator("#dividend-facts").is_visible():
            report["blockers"].append("Dividend fact panel did not become visible")
        for value in ["0", "4.99", "5", "9.99", "10", "24.99", "25", "49.99", "50", "100"]:
            form.locator("input[name=ownership_percent]").fill(value)
            page.wait_for_timeout(20)
        form.locator("input[name=ownership_percent]").fill("25")
        page.wait_for_timeout(100)
        if page.locator("select[name=direct_ownership]").is_visible():
            for value in ["true", "false"]:
                form.locator("select[name=direct_ownership]").select_option(value)
            form.locator("select[name=direct_ownership]").select_option("true")
        if page.locator("select[name=holding_period_mode]").is_visible():
            for value in ["known_date", "unknown_date"]:
                form.locator("select[name=holding_period_mode]").select_option(value)
                page.wait_for_timeout(60)
            form.locator("select[name=holding_period_mode]").select_option("known_date")
            page.wait_for_timeout(60)
            if form.locator("input[name=acquisition_date]").is_visible():
                form.locator("input[name=acquisition_date]").fill("2024-01-01")
        if form.locator("input[name=voting_ownership_percent]").is_visible():
            for value in ["0", "10", "25", "50", "100"]:
                form.locator("input[name=voting_ownership_percent]").fill(value)
            form.locator("input[name=voting_ownership_percent]").fill("25")
        tested.append("dividend_boundaries_and_modes")

        form.locator("select[name=income_type]").select_option("interest")
        page.wait_for_timeout(100)
        if not page.locator("#interest-facts").is_visible():
            report["blockers"].append("Interest fact panel did not become visible")
        for value in ["true", "false"]:
            form.locator("select[name=arm_length_amount]").select_option(value)
        form.locator("select[name=arm_length_amount]").select_option("true")
        for value in ["0", "9999", "100000", "1000000"]:
            form.locator("input[name=prior_same_type_monthly_amount_czk]").fill(value)
        form.locator("input[name=prior_same_type_monthly_amount_czk]").fill("0")
        tested.append("interest_all_ui_options")

        form.locator("select[name=income_type]").select_option("royalty")
        page.wait_for_timeout(100)
        if not page.locator("#royalty-facts").is_visible():
            report["blockers"].append("Royalty fact panel did not become visible")
        for category in ROYALTY_CATEGORIES:
            form.locator("select[name=royalty_category]").select_option(category)
        form.locator("select[name=royalty_category]").select_option(
            "patent_trademark_design_model_plan_secret_formula_process_or_knowhow"
        )
        tested.append("all_royalty_categories")

        # Real browser calculation + follow-up answering + report popup.
        form.locator("select[name=income_type]").select_option("dividend")
        form.locator("input[name=transaction_date]").fill("2026-08-12")
        form.locator("input[name=amount]").fill("100000")
        form.locator("select[name=currency]").select_option("CZK")
        form.locator("input[name=beneficial_owner][value=true]").check()
        form.locator("input[name=treaty_resident][value=true]").check()
        form.locator("input[name=pe_connection][value=false]").check()
        form.locator("input[name=ownership_percent]").fill("11")
        page.wait_for_timeout(100)
        if form.locator("select[name=direct_ownership]").is_visible():
            form.locator("select[name=direct_ownership]").select_option("true")
        if form.locator("select[name=holding_period_mode]").is_visible():
            form.locator("select[name=holding_period_mode]").select_option("known_date")
            page.wait_for_timeout(60)
            if form.locator("input[name=acquisition_date]").is_visible():
                form.locator("input[name=acquisition_date]").fill("2024-01-01")
        if form.locator("input[name=voting_ownership_percent]").is_visible():
            form.locator("input[name=voting_ownership_percent]").fill("11")

        for _ in range(4):
            page.locator("#workspace-submit").click()
            page.wait_for_timeout(700)
            if page.locator(".flow-step[data-step='4']").is_visible():
                break
            if page.locator("#workspace-follow-up").is_visible():
                questions = page.locator("#workspace-questions")
                for select in questions.locator("select").all():
                    values = select.locator("option").evaluate_all("(els) => els.map(e => e.value).filter(Boolean)")
                    if values:
                        select.select_option(values[0])
                for radio_name in questions.locator("input[type=radio]").evaluate_all(
                    "(els) => [...new Set(els.map(e => e.name).filter(Boolean))]"
                ):
                    radios = questions.locator(f"input[type=radio][name='{radio_name}']")
                    if radios.count():
                        radios.first.check()
                for inp in questions.locator("input[type=date]").all():
                    inp.fill("2024-01-01")
                for inp in questions.locator("input[type=number]").all():
                    inp.fill("25")
            else:
                break

        if not page.locator(".flow-step[data-step='4']").is_visible():
            report["blockers"].append("Representative AT dividend browser flow did not reach result step")
        else:
            result_status = page.locator("#workspace-result-status").inner_text().strip()
            browser_report["representative_result_status"] = result_status
            if "ČEKÁ NA VÝPOČET" in result_status:
                report["blockers"].append("Representative browser result remained in waiting state")
            if page.locator("#workspace-error").is_visible():
                report["blockers"].append(
                    "Representative browser calculation displayed error: "
                    + page.locator("#workspace-error").inner_text()
                )
            # Language switch after result.
            if page.locator("#taxtreat-language-controls button[data-lang='en']").count():
                page.locator("#taxtreat-language-controls button[data-lang='en']").click()
                page.wait_for_timeout(700)
                if page.evaluate("document.documentElement.lang") != "en":
                    report["blockers"].append("Language switch failed on result step")
                page.locator("#taxtreat-language-controls button[data-lang='cs']").click()
                page.wait_for_timeout(500)

            # Report history should be produced and print/PDF action should open a populated popup.
            page.locator("[data-nav='reviews']").first.click()
            page.wait_for_timeout(800)
            print_button = page.locator("button", has_text="Tisk / PDF").first
            if print_button.count() == 0:
                report["blockers"].append("No Tisk / PDF report action appeared after completed calculation")
            else:
                try:
                    with context.expect_page(timeout=4000) as popup_info:
                        print_button.click()
                    popup = popup_info.value
                    popup.wait_for_load_state("domcontentloaded", timeout=5000)
                    popup_html = popup.content()
                    browser_report["report_popup_html_length"] = len(popup_html)
                    if len(popup_html) < 1000:
                        report["blockers"].append("Report popup opened but contained suspiciously little HTML")
                    popup.close()
                    tested.append("report_popup_print_flow")
                except PlaywrightTimeoutError:
                    report["blockers"].append("Tisk / PDF action did not open a report window")

        # Inventory live controls after all dynamic layers loaded.
        inventory = page.evaluate(
            """() => [...document.querySelectorAll('button,select,input,a[href]')].map(el => ({
                tag: el.tagName,
                id: el.id || null,
                name: el.name || null,
                type: el.type || null,
                text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0,120),
                hidden: !!(el.hidden || el.closest('[hidden]')),
                disabled: !!el.disabled
            }))"""
        )
        browser_report["interactive_inventory_count"] = len(inventory)
        browser_report["interactive_inventory"] = inventory
        browser_report["tested_groups"] = tested
        browser_report["page_errors"] = page_errors
        browser_report["console_errors"] = console_errors

        if page_errors:
            report["blockers"].append(f"Browser produced {len(page_errors)} uncaught page errors")
        # Ignore browser messages caused solely by intentionally invalid external ARES/CNB network in CI.
        meaningful_console = [
            message for message in console_errors
            if "Failed to load resource" not in message
        ]
        browser_report["meaningful_console_errors"] = meaningful_console
        if meaningful_console:
            report["blockers"].append(f"Browser produced {len(meaningful_console)} console errors")

        browser.close()


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "created_at": "2026-09-02",
        "purpose": "Exhaustive live local web/API interaction audit before external deployment",
        "api": {},
        "browser": {},
        "blockers": [],
        "warnings": [],
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8765"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_for_server()
        run_api_matrix(report)
        run_browser_audit(report)
    except Exception as exc:
        report["blockers"].append(f"Audit harness exception: {exc!r}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "blocker_count": len(report["blockers"]),
        "blockers": report["blockers"],
        "api_matrix_requests": report.get("api", {}).get("matrix_request_count"),
        "api_hard_failures": report.get("api", {}).get("hard_failure_count"),
        "browser_tested_groups": report.get("browser", {}).get("tested_groups"),
        "public_source_countries": report.get("browser", {}).get("public_source_countries"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
