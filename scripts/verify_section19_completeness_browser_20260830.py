from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8769
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
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.set_default_timeout(7000)
            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")

            page.locator("[data-start-flow]").first.click()
            page.locator('.flow-step[data-step="1"] [data-next-step="2"]').click()
            page.locator('.flow-step[data-step="2"] [data-next-step="3"]').click()

            form = page.locator("#workspace-payment")
            form.locator('select[name="income_type"]').select_option("dividend")
            form.locator('input[name="transaction_date"]').fill("2026-08-11")
            form.locator('input[name="amount"]').fill("100000")
            form.locator('input[name="ownership_percent"]').fill("25")
            form.locator('select[name="direct_ownership"]').select_option("true")
            form.locator('select[name="holding_period_mode"]').select_option("known_date")
            form.locator('input[name="acquisition_date"]').fill("2024-01-01")
            treaty_resident_yes = form.locator('input[name="treaty_resident"][value="true"]')
            treaty_resident_yes.evaluate(
                "el => { el.checked = true; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }"
            )

            company_form = form.locator('select[name="section19_company_form"]')
            taxable_company = form.locator('select[name="section19_taxable_company"]')
            if not company_form.get_attribute("required") and company_form.get_attribute("aria-required") != "true":
                raise AssertionError("Section 19 company-form fact is not marked required for CZ dividends.")
            if not taxable_company.get_attribute("required") and taxable_company.get_attribute("aria-required") != "true":
                raise AssertionError("Section 19 tax-status fact is not marked required for CZ dividends.")

            form.locator("#workspace-submit").click()
            page.wait_for_timeout(150)

            if page.locator('.flow-step[data-step="4"].active').is_visible():
                raise AssertionError("CZ dividend reached the result while Section 19 facts were incomplete.")
            error = page.locator("#workspace-error")
            if error.is_hidden() or "§ 19" not in error.inner_text():
                raise AssertionError("Incomplete Section 19 facts did not produce the expected fail-closed error.")

            # Completing both facts must release the guard and allow the normal engine path.
            company_form.select_option("true")
            taxable_company.select_option("false")
            form.locator("#workspace-submit").click()
            page.locator('.flow-step[data-step="4"].active').wait_for(state="visible")

            browser.close()

        print("Section 19 completeness browser acceptance: PASS")
        return 0
    finally:
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
