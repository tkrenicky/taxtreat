from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import Page, BrowserContext, sync_playwright


BASE_URL = os.environ.get("TAXTREAT_LIVE_BASE_URL", "https://taxtreat.vercel.app").rstrip("/")
ARTIFACT_DIR = Path(os.environ.get("TAXTREAT_LIVE_E2E_ARTIFACT_DIR", "artifacts/live-production-e2e"))
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

INCOMES = ("dividend", "interest", "royalty")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def screenshot(page: Page, name: str) -> None:
    try:
        page.screenshot(path=str(ARTIFACT_DIR / f"{name}.png"), full_page=True)
    except Exception:
        pass


def fill_section19_if_present(page: Page) -> None:
    controls = page.locator("#cz-section19-facts select")
    for index in range(controls.count()):
        control = controls.nth(index)
        if control.is_visible() and not control.input_value():
            values = control.locator("option").evaluate_all(
                "(opts) => opts.map(o => o.value).filter(Boolean)"
            )
            preferred = "true" if "true" in values else (values[0] if values else None)
            if preferred:
                control.select_option(preferred)


def fill_dynamic_questions(page: Page) -> None:
    for round_no in range(15):
        if page.locator('.flow-step[data-step="4"].active').count():
            return

        questions = page.locator("#workspace-questions [data-input-path]")
        count = questions.count()
        if count == 0:
            page.wait_for_timeout(250)
            continue

        print(f"    follow-up round {round_no + 1}: {count} question(s)")

        for index in range(count):
            item = questions.nth(index)
            tag = item.evaluate("node => node.tagName")
            input_type = item.get_attribute("type")

            if tag == "SELECT":
                options = item.locator("option")
                path = item.get_attribute("data-input-path") or ""
                chosen = None

                # Standard Slovak corporate dividend path under Section 12(7)(c):
                # the distribution is not tax-deductible for the payer and is
                # not a special Section 3(1)(f) profit share.
                if path in {
                    "facts.distribution_is_tax_deductible_for_payer",
                    "facts.distribution_category_is_section_3_1_f",
                }:
                    chosen = "false"
                else:
                    for option_index in range(options.count()):
                        value = options.nth(option_index).get_attribute("value")
                        if value in ("true", "yes", "1"):
                            chosen = value
                            break

                if chosen is None and options.count() > 1:
                    chosen = options.nth(1).get_attribute("value")
                if chosen is not None:
                    item.select_option(chosen)
            elif input_type == "date":
                item.fill("2025-01-01")
            elif input_type in ("checkbox", "radio"):
                item.check()
            elif input_type == "number":
                item.fill("25")
            else:
                item.fill("25")

        fill_section19_if_present(page)
        page.locator("#workspace-submit").click()
        page.wait_for_timeout(350)

    raise AssertionError("Client-answerable questions did not resolve to the result step")


def start_flow(page: Page) -> None:
    start = page.locator("[data-start-flow]:visible")
    if start.count() == 0:
        page.locator('[data-nav="dashboard"]:visible').first.click()
        page.wait_for_function(
            "() => Boolean(document.querySelector('[data-view=\"dashboard\"].active'))"
        )
        start = page.locator("[data-start-flow]:visible")
    check(start.count() > 0, "No visible New calculation control is available")
    start.first.click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"1\"].active'))"
    )
    page.locator('[data-next-step="2"]:visible').click()
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )


def fill_case(page: Page, income: str) -> None:
    form = page.locator("#workspace-payment")
    form.locator('[name="income_type"]').select_option(income)
    form.locator('[name="transaction_date"]').fill("2026-09-02")
    form.locator('[name="amount"]').fill("100000")

    form.locator('label:has([name="treaty_resident"][value="true"])').click()

    check(
        form.locator('[name="beneficial_owner"][value="true"]').is_checked(),
        "beneficial_owner should default to true",
    )
    check(
        form.locator('[name="pe_connection"][value="false"]').is_checked(),
        "PE connection should default to false",
    )

    if income == "dividend":
        page.wait_for_function("() => !document.querySelector('#dividend-facts').hidden")
        form.locator('[name="ownership_percent"]').fill("25")
        page.wait_for_timeout(100)

        direct = form.locator('[name="direct_ownership"]')
        if direct.is_visible():
            direct.select_option("true")
        page.wait_for_timeout(100)

        holding = form.locator('[name="holding_period_mode"]')
        if holding.is_visible():
            holding.select_option("known_date")
        page.wait_for_timeout(100)

        acquisition = form.locator('[name="acquisition_date"]')
        if acquisition.is_visible():
            acquisition.fill("2024-01-01")

        voting = form.locator('[name="voting_ownership_percent"]')
        if voting.is_visible():
            voting.fill("25")

        fill_section19_if_present(page)

    elif income == "interest":
        page.wait_for_function("() => !document.querySelector('#interest-facts').hidden")
        arm_length = form.locator('[name="arm_length_amount"]')
        if arm_length.count():
            arm_length.select_option("true")

    elif income == "royalty":
        page.wait_for_function("() => !document.querySelector('#royalty-facts').hidden")
        form.locator('[name="royalty_category"]').select_option("computer_software")


def invalid_controls(page: Page) -> list[dict]:
    return page.evaluate(
        """
        () => [...document.querySelectorAll('#workspace-payment :invalid')].map(el => ({
          tag: el.tagName,
          name: el.name || null,
          id: el.id || null,
          type: el.type || null,
          value: el.value,
          required: el.required,
          visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
        }))
        """
    )


def run_case(
    page: Page,
    context: BrowserContext,
    source: str,
    income: str,
    captured_payloads: list[dict],
) -> None:
    print(f"\n=== LIVE CASE {source}/{income} ===")
    start_flow(page)
    fill_case(page, income)

    invalid = invalid_controls(page)
    check(not invalid, f"{source}/{income}: invalid controls before submit: {invalid}")

    before = len(captured_payloads)
    page.locator("#workspace-submit").click()

    page.wait_for_function(
        """
        () => Boolean(
          document.querySelector('.flow-step[data-step="4"].active') ||
          !document.querySelector('#workspace-follow-up').hidden ||
          !document.querySelector('#workspace-error').hidden
        )
        """
    )

    if page.locator("#workspace-error").is_visible():
        message = page.locator("#workspace-error").inner_text().strip()
        raise AssertionError(f"{source}/{income}: UI error after submit: {message}")

    fill_dynamic_questions(page)

    check(
        page.locator('.flow-step[data-step="4"].active').count() == 1,
        f"{source}/{income}: result step not reached",
    )
    check(
        len(captured_payloads) > before,
        f"{source}/{income}: no /analysis/intake POST captured",
    )

    payload = captured_payloads[-1]
    check(payload.get("source_country") == source, f"{source}/{income}: source-country payload mismatch")
    check(payload.get("income_type") == income, f"{source}/{income}: income payload mismatch")

    legal_ref = page.locator(".compliance-schedule .card-head span").inner_text().strip()
    tax_label = page.locator("#workspace-tax-label").inner_text().strip()
    print("    tax label:", tax_label)
    print("    legal reference:", legal_ref)

    if source == "CZ":
        check(
            ("586/1992" in legal_ref) or ("§ 38d" in legal_ref and "ZDP" in legal_ref),
            f"CZ/{income}: Czech legal reference missing: {legal_ref}",
        )
        check("595/2003" not in legal_ref, f"CZ/{income}: Slovak legal reference leaked")
        check(page.locator('#workspace-payment [name="currency"]').input_value() == "CZK", "CZ currency mismatch")
    else:
        check("595/2003" in legal_ref, f"SK/{income}: Slovak legal reference missing")
        check("586/1992" not in legal_ref, f"SK/{income}: Czech legal reference leaked")
        check(page.locator('#workspace-payment [name="currency"]').input_value() == "EUR", "SK currency mismatch")

        if income == "dividend":
            check(
                page.locator("#cz-section19-facts:visible").count() == 0,
                "SK/dividend: Czech Section 19 controls are visible",
            )
            check(
                "Není předmětem daně" in page.locator("#workspace-tax").inner_text(),
                "SK/dividend: standard corporate dividend did not resolve to outside-subject treatment",
            )
            check(
                "§ 12" in page.locator("#workspace-citations").inner_text(),
                "SK/dividend: Section 12 legal basis missing from result",
            )

    report_response = context.request.post(
        BASE_URL + "/analysis/report",
        data=payload,
        headers={"Content-Type": "application/json"},
        timeout=20_000,
    )
    check(report_response.ok, f"{source}/{income}: /analysis/report HTTP {report_response.status}")

    body = report_response.json()
    check(bool(body.get("html")), f"{source}/{income}: report HTML missing")
    check(bool(body.get("report")), f"{source}/{income}: report object missing")

    report = body["report"]
    scope = report.get("scope") or {}
    check(scope.get("recipient_country") == payload.get("recipient_country"), f"{source}/{income}: report recipient mismatch")
    check(scope.get("income_type") == income, f"{source}/{income}: report income mismatch")

    html = body["html"]
    if source == "CZ":
        check("595/2003" not in html, f"CZ/{income}: Slovak statute leaked into report")
    else:
        check("586/1992" not in html, f"SK/{income}: Czech statute leaked into report")

    print("    report id:", report.get("report_id"))
    print("    report html bytes:", len(html))
    print(f"PASS {source}/{income}")


def stable_locale_check(browser, path: str, expected_lang: str) -> None:
    page = browser.new_page()
    page.set_default_timeout(12_000)
    errors: list[str] = []
    failed: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("requestfailed", lambda r: failed.append(f"{r.method} {r.url} :: {r.failure}"))

    response = page.goto(BASE_URL + path, wait_until="domcontentloaded", timeout=20_000)
    check(bool(response and response.ok), f"{path}: page load failed")
    page.wait_for_function(
        "() => Boolean(window.TaxTreatWorkspaceSourceCountry && window.TaxTreatSourceCountries)"
    )
    page.wait_for_timeout(4_000)

    check(page.evaluate("document.documentElement.lang") == expected_lang, f"{path}: lang mismatch")
    check(page.locator("#tt-bootstrap-warning").count() == 0, f"{path}: bootstrap warning shown")
    check(not errors, f"{path}: console errors {errors}")
    check(not failed, f"{path}: request failures {failed}")
    page.close()


def create_sk_payer(page: Page) -> None:
    page.locator('[data-nav="payers"]').click()
    page.locator("[data-create-payer]:visible").click()

    form = page.locator("#payer-form")
    form.locator('[name="payer_id"]').fill("12345679")
    form.locator('[name="payer_name"]').fill("Live QA SK s.r.o.")
    form.locator('[name="payer_vat_id"]').fill("SK2020000000")
    form.locator('[name="payer_country"]').select_option("SK")
    form.locator("[data-save-payer]").click()

    page.wait_for_function("() => document.body.dataset.sourceCountry === 'SK'")
    page.wait_for_function(
        """() => document.querySelectorAll(
            '#new-recipient-form [name="recipient_country"] option'
        ).length === 76"""
    )


def main() -> int:
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )

            stable_locale_check(browser, "/ui/cs", "cs")
            stable_locale_check(browser, "/ui/en", "en")
            print("\nPASS stable CS/EN bootstrap")

            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = context.new_page()
            page.set_default_timeout(12_000)
            page.set_default_navigation_timeout(20_000)

            console_errors: list[str] = []
            captured_payloads: list[dict] = []

            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error" and "favicon" not in message.text.lower()
                else None,
            )

            def record_request(request) -> None:
                if "/analysis/intake" in request.url and request.method == "POST":
                    try:
                        captured_payloads.append(request.post_data_json)
                    except Exception:
                        pass

            page.on("request", record_request)

            response = page.goto(BASE_URL + "/ui/cs", wait_until="domcontentloaded", timeout=20_000)
            check(bool(response and response.ok), "CZ workspace failed to load")
            page.wait_for_function("() => Boolean(window.TaxTreatWorkspaceSourceCountry)")
            page.wait_for_function("() => document.body.dataset.sourceCountry === 'CZ'")
            page.wait_for_function(
                """() => document.querySelectorAll(
                    '#new-recipient-form [name="recipient_country"] option'
                ).length === 102"""
            )
            page.wait_for_timeout(2_500)

            for income in INCOMES:
                run_case(page, context, "CZ", income, captured_payloads)

            create_sk_payer(page)
            page.wait_for_timeout(1_000)

            sk_context = page.evaluate("window.TaxTreatWorkspaceSourceCountry.getActiveContext()")
            check(sk_context["baseCurrency"] == "EUR", "SK base currency mismatch")
            check(sk_context["complianceFormCode"] == "OZN4311v26", "SK compliance form mismatch")

            page.reload(wait_until="domcontentloaded", timeout=20_000)
            page.wait_for_function("() => document.body.dataset.sourceCountry === 'SK'")
            page.locator('[data-nav="sources"]').click()
            metrics = page.locator('[data-view="sources"] .source-metrics strong')
            values = [metrics.nth(i).inner_text().strip() for i in range(2)]
            check(values == ["75", "225"], f"SK source metrics mismatch: {values}")

            for income in INCOMES:
                run_case(page, context, "SK", income, captured_payloads)

            check(not console_errors, f"browser console errors: {console_errors}")

            screenshot(page, "final-state")
            browser.close()

        summary = {
            "base_url": BASE_URL,
            "locales": ["cs", "en"],
            "sources": ["CZ", "SK"],
            "income_types": list(INCOMES),
            "live_cases": 6,
            "status": "PASS",
        }
        (ARTIFACT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("\nLIVE_PRODUCTION_E2E_OK")
        return 0
    except Exception as exc:
        print(f"\nLIVE_PRODUCTION_E2E_FAILED: {exc!r}")
        traceback.print_exc()
        try:
            if "page" in locals():
                screenshot(page, "failure")
                state = {
                    "url": page.url,
                    "body_source_country": page.evaluate("document.body.dataset.sourceCountry"),
                    "invalid_controls": invalid_controls(page),
                    "workspace_error": page.locator("#workspace-error").inner_text()
                    if page.locator("#workspace-error").count()
                    else "",
                }
                (ARTIFACT_DIR / "failure-state.json").write_text(
                    json.dumps(state, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
