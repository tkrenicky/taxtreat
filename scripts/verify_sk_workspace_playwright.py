from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("TAXTREAT_E2E_PORT", "8765"))
BASE_URL = f"http://127.0.0.1:{PORT}"


def fail(message: str) -> None:
    raise AssertionError(message)


def wait_for_server(process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            fail("local TaxTreat server exited before becoming ready")
        try:
            urlopen(f"{BASE_URL}/health/live", timeout=1).read()
            return
        except Exception:
            time.sleep(0.25)
    fail("local TaxTreat server did not become ready")


def fill_client_questions(page) -> None:
    for _ in range(8):
        questions = page.locator("#workspace-questions [data-input-path]")
        count = questions.count()
        if count == 0:
            return
        for index in range(count):
            item = questions.nth(index)
            tag = item.evaluate("node => node.tagName")
            if tag == "SELECT":
                item.select_option(index=1)
            elif item.get_attribute("type") == "date":
                item.fill("2025-01-01")
            else:
                item.fill("25")
        page.locator("#workspace-submit").click()
        page.wait_for_timeout(250)
        if page.locator('.flow-step[data-step="4"].active').count():
            return
    fail("SK browser flow did not resolve its client-answerable questions")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("BROWSER_SMOKE_UNAVAILABLE: Python package 'playwright' is not installed.")
        return 2

    server_log = Path("/tmp/taxtreat-sk-e2e-uvicorn.log")
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(PORT),
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

    try:
        wait_for_server(server)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.set_default_timeout(10_000)
            page.set_default_navigation_timeout(10_000)
            console_errors: list[str] = []
            sk_intake_payloads: list[dict] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )

            def record_request(request) -> None:
                if request.url.endswith("/analysis/intake") and request.post_data_json:
                    sk_intake_payloads.append(request.post_data_json)

            page.on("request", record_request)
            page.goto(f"{BASE_URL}/ui", wait_until="domcontentloaded")
            page.wait_for_function(
                """() => Boolean(
                    window.TaxTreatWorkspaceSourceCountry &&
                    window.TaxTreatSourceCountries?.countries?.SK &&
                    document.querySelector('#payer-form [name=payer_country]') &&
                    document.querySelector('#taxtreat-language-controls [data-lang=en]')
                )"""
            )
            page.wait_for_function(
                """() => document.querySelectorAll(
                    '#new-recipient-form [name="recipient_country"] option'
                ).length === 102"""
            )

            assert page.evaluate("document.body.dataset.sourceCountry") == "CZ"
            assert page.locator(
                '#new-recipient-form [name="recipient_country"] option'
            ).count() == 102

            page.locator("[data-create-payer]").first.click()
            payer = page.locator("#payer-form")
            payer.locator('[name="payer_id"]').fill("12345678")
            payer.locator('[name="payer_name"]').fill("Demo SK s.r.o.")
            payer.locator('[name="payer_vat_id"]').fill("SK2020000000")
            payer.locator('[name="payer_country"]').select_option("SK")
            payer.locator("[data-save-payer]").click()

            page.wait_for_function(
                "() => document.body.dataset.sourceCountry === 'SK'"
            )
            page.wait_for_function(
                """() => document.querySelectorAll(
                    '#new-recipient-form [name="recipient_country"] option'
                ).length === 76"""
            )

            context = page.evaluate(
                "window.TaxTreatWorkspaceSourceCountry.getActiveContext()"
            )
            assert context["runtimeReleased"] is True
            assert context["baseCurrency"] == "EUR"
            assert context["complianceFormCode"] == "OZN4311v26"
            assert page.locator("#workspace-submit").get_attribute("aria-disabled") == "false"
            assert page.locator('#workspace-payment [name="currency"]').input_value() == "EUR"
            assert page.locator("#workspace-exchange-rate-field").is_hidden()

            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.body.dataset.sourceCountry === 'SK'"
            )
            page.wait_for_function(
                """() => document.querySelectorAll(
                    '#new-recipient-form [name="recipient_country"] option'
                ).length === 76"""
            )
            assert page.locator("#active-payer-select").input_value().startswith("payer-")
            assert page.locator('#workspace-payment [name="currency"]').input_value() == "EUR"

            page.locator('[data-nav="sources"]').click()
            metrics = page.locator('[data-view="sources"] .source-metrics strong')
            assert [metrics.nth(i).inner_text().strip() for i in range(2)] == ["75", "225"]

            page.locator('#taxtreat-language-controls [data-lang="en"]').click()
            page.wait_for_function("() => document.documentElement.lang === 'en'")
            assert "Slovak entities" in page.locator(
                '[data-view="payers"] .page-title span'
            ).inner_text()
            assert "Supported jurisdictions" in page.locator(
                '[data-view="sources"] .source-metrics span'
            ).first.inner_text()

            page.locator('#taxtreat-language-controls [data-lang="cs"]').click()
            page.wait_for_function("() => document.documentElement.lang === 'cs'")
            page.locator("[data-start-flow]").first.click()
            page.locator('[data-next-step="2"]:visible').click()
            page.locator('[data-next-step="3"]:visible').click()

            form = page.locator("#workspace-payment")
            form.locator('[name="income_type"]').select_option("interest")
            form.locator('[name="transaction_date"]').fill("2026-09-02")
            form.locator('[name="amount"]').fill("100000")
            form.locator('[name="treaty_resident"][value="true"]').check()
            form.locator('[name="beneficial_owner"][value="true"]').check()
            form.locator('[name="pe_connection"][value="false"]').check()
            form.locator('[name="arm_length_amount"]').select_option("true")
            form.locator("#workspace-submit").click()
            page.wait_for_function(
                """() => Boolean(
                    document.querySelector('.flow-step[data-step="4"].active') ||
                    !document.querySelector('#workspace-follow-up').hidden
                )"""
            )
            fill_client_questions(page)
            page.wait_for_function(
                "() => Boolean(document.querySelector('.flow-step[data-step=\"4\"].active'))"
            )

            if not sk_intake_payloads:
                fail("SK browser flow did not submit /analysis/intake")
            submitted = sk_intake_payloads[-1]
            assert submitted["source_country"] == "SK"
            sk_partner_codes = {
                option.get_attribute("value")
                for option in page.locator(
                    '#new-recipient-form [name="recipient_country"] option'
                ).all()
            }
            assert submitted["recipient_country"] in sk_partner_codes
            assert submitted["transaction_amount"]["currency"] == "EUR"

            assert "Zrážková daň" in page.locator("#workspace-tax-label").inner_text()
            legal_reference = page.locator(
                ".compliance-schedule .card-head span"
            ).inner_text()
            assert "595/2003" in legal_reference
            assert "586/1992" not in legal_reference

            page.locator('#taxtreat-language-controls [data-lang="en"]').click()
            page.wait_for_function("() => document.documentElement.lang === 'en'")
            assert "Slovak withholding tax" in page.locator(
                "#workspace-tax-label"
            ).inner_text()

            page.locator("#active-payer-select").select_option("demo-cz")
            page.wait_for_function(
                "() => document.body.dataset.sourceCountry === 'CZ'"
            )
            page.wait_for_function(
                """() => document.querySelectorAll(
                    '#new-recipient-form [name="recipient_country"] option'
                ).length === 102"""
            )
            assert page.locator('#workspace-payment [name="currency"]').input_value() == "CZK"

            relevant_errors = [
                error for error in console_errors if "favicon" not in error.lower()
            ]
            if relevant_errors:
                fail(f"browser console errors: {relevant_errors}")
            browser.close()

        print("SK_WORKSPACE_BROWSER_OK")
        return 0
    except Exception as exc:
        print(f"SK_WORKSPACE_BROWSER_FAILED: {exc}")
        if server_log.exists():
            print(server_log.read_text(encoding="utf-8", errors="replace"))
        return 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
