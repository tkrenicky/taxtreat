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


def check(page, label: str, expression: str) -> None:
    result = page.evaluate(expression)
    if result is True:
        print(f"PASS: {label}")
        return
    fail(f"{label}: {result!r}")


def wait_for_server(process: subprocess.Popen[str]) -> None:
    for _ in range(20):
        if process.poll() is not None:
            fail("local TaxTreat server exited before becoming ready")
        try:
            urlopen(f"{BASE_URL}/health/live", timeout=1).read()
            return
        except Exception:
            time.sleep(0.5)
    fail("local TaxTreat server did not become ready")


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
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(headless=True)
            except Exception as exc:
                print(f"BROWSER_SMOKE_UNAVAILABLE: Chromium is not installed for Playwright: {exc}")
                return 2

            page = browser.new_page()
            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")

            check(page, "initial CZ source country", '() => document.body.dataset.sourceCountry === "CZ"')
            check(page, "initial CZ currency", '() => document.querySelector("#workspace-payment [name=currency]").value === "CZK"')
            check(page, "initial CZ runtime released", '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().runtimeReleased === true')

            page.evaluate('''() => { const s=document.querySelector("#active-source-country"); s.value="SK"; s.dispatchEvent(new Event("change", {bubbles:true})); }''')
            page.wait_for_timeout(150)

            check(page, "SK source country", '() => document.body.dataset.sourceCountry === "SK"')
            check(page, "SK EUR currency", '() => document.querySelector("#workspace-payment [name=currency]").value === "EUR"')
            check(page, "SK runtime remains prerelease", '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().runtimeReleased === false')
            check(page, "SK submit is disabled semantically", '() => document.querySelector("#workspace-submit").getAttribute("aria-disabled") === "true"')
            check(page, "SK submit copy", '() => document.querySelector("#workspace-submit").textContent.includes("Slovenský výpočet zatím není vydán")')
            check(page, "SK FX field hidden", '() => document.querySelector("#workspace-exchange-rate-field").hidden === true')
            check(page, "SK compliance form", '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().complianceFormCode === "OZN4311v26"')
            check(page, "SK 15-day compliance deadline", '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().notificationDeadlineRule === "15th_day_of_following_calendar_month" && window.TaxTreatWorkspaceSourceCountry.getActiveContext().remittanceDeadlineRule === "15th_day_of_following_calendar_month"')
            check(page, "SK ordinary annual WHT return not configured", '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().ordinaryAnnualWhtReturnConfigured === false')

            page.evaluate('() => document.querySelector("[data-nav=payers]").click()')
            page.wait_for_timeout(100)
            check(page, "SK payer page copy", '() => document.querySelector("[data-view=payers] .page-title span").textContent.includes("Slovenské subjekty")')

            page.evaluate('() => document.querySelector("[data-nav=recipients]").click()')
            page.evaluate('() => document.querySelector("[data-view=recipients] [data-open-recipient]").click()')
            page.wait_for_timeout(100)
            check(page, "SK PE label", '() => [...document.querySelectorAll("[data-view=recipient-detail] dt")].some(n => n.textContent.includes("Väzba príjmu na stálu prevádzkareň v SR"))')

            page.evaluate('() => document.querySelector("[data-nav=sources]").click()')
            page.wait_for_timeout(100)
            check(page, "SK source metrics 75 / 225", '() => { const a=[...document.querySelectorAll("[data-view=sources] .source-metrics strong")].map(n=>n.textContent.trim()); return a[0] === "75" && a[1] === "225"; }')

            page.evaluate('''() => { const s=document.querySelector("#active-source-country"); s.value="CZ"; s.dispatchEvent(new Event("change", {bubbles:true})); }''')
            page.wait_for_timeout(150)
            check(page, "return to CZ source country", '() => document.body.dataset.sourceCountry === "CZ"')
            check(page, "return to CZ currency", '() => document.querySelector("#workspace-payment [name=currency]").value === "CZK"')
            check(page, "return to CZ source metrics 101 / 303", '() => { const a=[...document.querySelectorAll("[data-view=sources] .source-metrics strong")].map(n=>n.textContent.trim()); return a[0] === "101" && a[1] === "303"; }')

            page.evaluate('() => document.querySelector("[data-nav=recipients]").click()')
            page.evaluate('() => document.querySelector("[data-view=recipients] [data-open-recipient]").click()')
            page.wait_for_timeout(100)
            check(page, "return to CZ PE label", '() => [...document.querySelectorAll("[data-view=recipient-detail] dt")].some(n => n.textContent.includes("Vazba ke stálé provozovně v ČR"))')

            browser.close()

        print("BROWSER_SMOKE_OK")
        return 0
    except Exception as exc:
        print(f"BROWSER_SMOKE_FAILED: {exc}")
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
