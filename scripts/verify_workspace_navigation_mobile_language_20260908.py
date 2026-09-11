from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8775
BASE_URL = f"http://{HOST}:{PORT}"


def wait_server(process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server exited: {process.returncode}")
        try:
            with urlopen(f"{BASE_URL}/health/live", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError("server not ready")


def assert_no_console_errors(errors: list[str]) -> None:
    relevant = [item for item in errors if "favicon" not in item.lower()]
    assert not relevant, relevant


def fill_payment_probe(page) -> None:
    form = page.locator("#workspace-payment")
    form.locator('[name="income_type"]').select_option("dividend")
    form.locator('[name="transaction_date"]').fill("2026-09-08")
    form.locator('[name="amount"]').fill("123456")
    form.locator('[name="treaty_resident"][value="true"]').check()
    form.locator('[name="ownership_percent"]').fill("25")
    form.locator('[name="direct_ownership"]').select_option("true")
    form.locator('[name="holding_period_mode"]').select_option("known_date")
    form.locator('[name="acquisition_date"]').fill("2024-01-01")
    form.locator('[name="voting_ownership_percent"]').fill("25")
    page.wait_for_selector('[name="section19_company_form"]')
    form.locator('[name="section19_company_form"]').select_option("true")
    form.locator('[name="section19_taxable_company"]').select_option("true")


def assert_payment_probe(page) -> None:
    form = page.locator("#workspace-payment")
    assert form.locator('[name="income_type"]').input_value() == "dividend"
    assert form.locator('[name="transaction_date"]').input_value() == "2026-09-08"
    assert form.locator('[name="amount"]').input_value() == "123456"


def main() -> int:
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_server(process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            page = browser.new_page(viewport={"width": 1365, "height": 900})
            desktop_errors: list[str] = []
            page.on("console", lambda msg: desktop_errors.append(msg.text) if msg.type == "error" else None)
            page.goto(f"{BASE_URL}/ui/cs", wait_until="networkidle")

            for nav in ("dashboard", "payers", "recipients", "reviews", "sources"):
                page.locator(f'[data-nav="{nav}"]:visible').first.click()
                page.wait_for_function(
                    "name => Boolean(document.querySelector(`[data-view=\"${name}\"]`)?.classList.contains('active'))",
                    arg=nav,
                )

            page.locator('[data-nav="recipients"]:visible').first.click()
            page.locator('[data-view="recipients"] [data-open-recipient]').click()
            page.wait_for_function("() => document.querySelector('[data-view=\"recipient-detail\"]')?.classList.contains('active')")
            page.locator('[data-view="recipient-detail"] [data-nav="recipients"]').click()
            page.wait_for_function("() => document.querySelector('[data-view=\"recipients\"]')?.classList.contains('active')")

            page.locator('[data-nav="dashboard"]:visible').first.click()
            page.locator('[data-start-flow]:visible').first.click()
            page.locator('.flow-step[data-step="1"] [data-next-step="2"]').click()
            page.locator('.flow-step[data-step="2"] [data-next-step="3"]').click()
            page.wait_for_function("() => document.querySelector('.flow-step[data-step=\"3\"]')?.classList.contains('active')")
            fill_payment_probe(page)

            # Finish a real calculation first. This is the production failure mode:
            # changing locale on step 4 must reconstruct the result in the target locale.
            page.locator("#workspace-submit").click()
            page.wait_for_function("() => document.querySelector('.flow-step[data-step=\"4\"]')?.classList.contains('active')")
            page.wait_for_function("() => !/ČEKÁ NA VÝPOČET|WAITING FOR CALCULATION/i.test(document.querySelector('#workspace-result-status')?.textContent || '')")

            page.wait_for_selector('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]', state="visible")
            page.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]').click()
            page.wait_for_url("**/ui/en")
            page.wait_for_function("() => document.documentElement.lang === 'en'")
            page.wait_for_function("() => document.querySelector('.flow-step[data-step=\"4\"]')?.classList.contains('active')")
            page.wait_for_function("() => !/FACTS REQUIRED|WAITING FOR CALCULATION/i.test(document.querySelector('#workspace-result-status')?.textContent || '')")
            assert page.locator('.flow-step[data-step="4"] h1').inner_text() == "Result"
            assert_payment_probe(page)
            assert page.evaluate("localStorage.getItem('taxtreat-ui-language')") == "en"

            page.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="cs"]').click()
            page.wait_for_url("**/ui/cs")
            page.wait_for_function("() => document.documentElement.lang === 'cs'")
            page.wait_for_function("() => document.querySelector('.flow-step[data-step=\"4\"]')?.classList.contains('active')")
            page.wait_for_function("() => !/ČEKÁ NA VÝPOČET/i.test(document.querySelector('#workspace-result-status')?.textContent || '')")
            assert page.locator('.flow-step[data-step="4"] h1').inner_text() == "Výsledek"
            assert_payment_probe(page)
            assert_no_console_errors(desktop_errors)
            page.close()

            mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
            mobile_errors: list[str] = []
            mobile.on("console", lambda msg: mobile_errors.append(msg.text) if msg.type == "error" else None)
            mobile.goto(f"{BASE_URL}/ui/cs", wait_until="networkidle")
            mobile.wait_for_timeout(500)

            overflow = mobile.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert overflow <= 8, f"mobile horizontal overflow: {overflow}px"

            mobile.locator('[data-start-flow]:visible').first.click()
            mobile.wait_for_function("() => document.querySelector('.flow-step[data-step=\"1\"]')?.classList.contains('active')")
            mobile.locator('.flow-step[data-step="1"] [data-next-step="2"]').click()
            mobile.wait_for_function("() => document.querySelector('.flow-step[data-step=\"2\"]')?.classList.contains('active')")
            mobile.locator('.flow-step[data-step="2"] [data-next-step="3"]').click()
            mobile.wait_for_function("() => document.querySelector('.flow-step[data-step=\"3\"]')?.classList.contains('active')")
            fill_payment_probe(mobile)

            mobile.wait_for_selector('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]', state="visible")
            mobile.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]').click()
            mobile.wait_for_url("**/ui/en")
            mobile.wait_for_function("() => document.documentElement.lang === 'en'")
            mobile.wait_for_function("() => document.querySelector('.flow-step[data-step=\"3\"]')?.classList.contains('active')")
            assert_payment_probe(mobile)
            assert_no_console_errors(mobile_errors)

            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    print("Workspace navigation/mobile/live-language QA: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
