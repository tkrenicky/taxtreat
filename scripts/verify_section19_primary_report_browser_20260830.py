from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8768
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
            page.on("popup", lambda popup: popup.close())
            page.goto(f"{BASE_URL}/ui/en", wait_until="networkidle")

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
            form.locator('input[name="voting_ownership_percent"]').fill("25")

            # The positive Section 19 branch is factually complete.
            form.locator('select[name="section19_company_form"]').select_option("true")
            form.locator('select[name="section19_taxable_company"]').select_option("true")
            with page.expect_response(lambda response: "/analysis/intake" in response.url) as analysis_response_info:
                form.locator("#workspace-submit").click()
            analysis_response = analysis_response_info.value
            if not analysis_response.ok:
                raise AssertionError(f"Analysis endpoint failed with HTTP {analysis_response.status}.")
            analysis_body = analysis_response.json()
            analysis = analysis_body.get("analysis") or {}
            if analysis.get("status") != "FINAL":
                raise AssertionError(
                    f"Positive Section 19 path is not FINAL: {analysis.get('status')!r}; "
                    f"missing={analysis.get('missing_facts')!r}"
                )
            if analysis.get("tax_treatment") != "domestic_exemption":
                raise AssertionError(
                    "Positive Section 19 path did not select domestic_exemption: "
                    f"{analysis.get('tax_treatment')!r}"
                )

            page.locator('.flow-step[data-step="4"].active').wait_for(state="visible")
            page.wait_for_timeout(500)
            result = page.locator('.flow-step[data-step="4"].active')
            text = result.inner_text()
            if "Domestic exemption" not in text:
                raise AssertionError(f"Positive Section 19 UI does not identify the domestic exemption. Result text: {text!r}")
            if "primary legal basis" not in text.lower():
                raise AssertionError(f"Section 19 is not presented as the primary legal basis in the EN result. Result text: {text!r}")

            report_button = page.get_by_role("button", name="Print / PDF report", exact=True)
            with page.expect_response(lambda response: response.url.endswith("/analysis/report")) as response_info:
                report_button.click()
            response = response_info.value
            if not response.ok:
                raise AssertionError(f"Report endpoint failed with HTTP {response.status}.")
            request_payload = response.request.post_data_json or {}
            request_facts = request_payload.get("facts") or {}
            report_language = request_facts.get("__report_language")
            body = response.json()
            report = body.get("report") or {}
            report_result = report.get("result") or {}
            html = str(body.get("html") or "")

            if report_result.get("status") != "FINAL":
                raise AssertionError(f"Section 19 report is not FINAL: {report_result.get('status')!r}")
            if report_result.get("tax_treatment") != "domestic_exemption":
                raise AssertionError(
                    f"Section 19 report treatment is not domestic_exemption: {report_result.get('tax_treatment')!r}"
                )
            if report_language != "en":
                raise AssertionError(
                    "Report request from /ui/en did not carry __report_language='en': "
                    f"{report_language!r}; document_lang={page.locator('html').get_attribute('lang')!r}; "
                    f"route_locale={page.evaluate('window.__TAXTREAT_LOCALE__')!r}"
                )
            if 'lang="en"' not in html:
                raise AssertionError(
                    "Report request carried EN locale but returned non-English HTML; "
                    f"report_language={report_language!r}"
                )
            if "domestic exemption" not in html.lower() or "primary legal basis" not in html.lower():
                raise AssertionError("English report does not present the domestic exemption as the primary legal basis.")
            supplementary = html.lower()
            if (
                "secondary treaty" not in supplementary
                and "treaty protection is secondary" not in supplementary
                and "treaty treatment is supplementary" not in supplementary
            ):
                raise AssertionError("English report does not identify treaty treatment as supplementary/secondary.")

            browser.close()

        print("Section 19 primary result/report browser acceptance: PASS")
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
