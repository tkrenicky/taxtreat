from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8766
BASE_URL = f"http://{HOST}:{PORT}"


def wait_for_server(process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"UI server exited with code {process.returncode}."
            )
        try:
            with urlopen(f"{BASE_URL}/health/live", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError("UI server did not become ready within 30 seconds.")


def finish_workspace_calculation(page) -> None:
    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
    page.get_by_role("button", name="Nová kontrola platby →").first.click()
    page.get_by_role("button", name="Pokračovat k příjemci →").click()
    page.get_by_role("button", name="Pokračovat k platbě →").click()

    form = page.locator("#workspace-payment")
    form.locator('select[name="income_type"]').select_option("dividend")
    form.locator('input[name="transaction_date"]').fill("2026-08-11")
    form.locator('input[name="amount"]').fill("100000")
    form.locator('select[name="currency"]').select_option("CZK")
    form.locator('input[name="ownership_percent"]').fill("25")
    form.locator('select[name="direct_ownership"]').select_option("true")
    form.locator('select[name="holding_period_mode"]').select_option(
        "known_date"
    )
    form.locator('input[name="acquisition_date"]').fill("2024-01-01")

    for _ in range(6):
        form.locator("#workspace-submit").click()
        page.wait_for_timeout(250)
        if page.locator('.flow-step[data-step="4"].active').is_visible():
            break
        questions = form.locator("#workspace-questions")
        for item in questions.locator("select").all():
            if item.locator("option").count() > 1:
                item.select_option(index=1)
        for item in questions.locator('input[type="number"]').all():
            item.fill("25")
        for item in questions.locator('input[type="date"]').all():
            item.fill("2024-01-01")
    else:
        raise AssertionError("Workspace client questions did not converge.")

    page.locator("#workspace-result-status").wait_for(state="visible")


def main() -> int:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_for_server(process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1100},
                locale="cs-CZ",
            )
            context.add_init_script(
                "window.print = () => { window.__taxtreatPrintCalled = true; };"
            )
            page = context.new_page()
            console_errors: list[str] = []
            report_requests: list[str] = []
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text)
                    if message.type == "error"
                    else None
                ),
            )
            page.on(
                "request",
                lambda request: (
                    report_requests.append(request.url)
                    if request.url.endswith("/analysis/report")
                    else None
                ),
            )

            finish_workspace_calculation(page)

            output_rows = page.locator("[data-output-report-id]")
            output_rows.first.wait_for(state="attached", timeout=5000)
            if output_rows.count() < 2:
                raise AssertionError(
                    "Completed result was not exposed on dashboard and outputs."
                )
            if not any("Dividendy · AT" in text for text in output_rows.all_inner_texts()):
                raise AssertionError(
                    "Output history is missing the transaction summary."
                )
            if len(report_requests) < 1:
                raise AssertionError(
                    "Completed result did not preload /analysis/report."
                )

            open_button = page.locator('[data-report-action="open"]')
            print_button = page.locator('[data-report-action="print"]')
            if open_button.count() != 1 or print_button.count() != 1:
                raise AssertionError("Workspace report actions are missing.")

            requests_before_direct_exports = len(report_requests)
            with page.expect_popup() as popup_info:
                open_button.click()
            report_page = popup_info.value
            report_page.wait_for_load_state("domcontentloaded")
            report_page.get_by_text("Česká srážková daň", exact=True).wait_for()
            if report_page.locator(".source").count() < 1:
                raise AssertionError(
                    "Opened professional report contains no legal sources."
                )
            if "TaxTreat" not in report_page.title():
                raise AssertionError("Opened report has an unexpected title.")
            report_page.close()

            with page.expect_popup() as print_popup_info:
                print_button.click()
            print_page = print_popup_info.value
            print_page.wait_for_function(
                "() => window.__taxtreatPrintCalled === true",
                timeout=5000,
            )
            if print_page.locator("details[open]").count() < 1:
                raise AssertionError(
                    "Print export did not expand legal provision details."
                )
            print_page.close()

            if len(report_requests) < requests_before_direct_exports + 2:
                raise AssertionError(
                    "Both result export actions must request /analysis/report."
                )

            page.get_by_role("button", name="Výstupy", exact=True).click()
            outputs_view = page.locator('[data-view="outputs"].active')
            outputs_view.wait_for(state="visible")
            stored_rows = outputs_view.locator("[data-output-report-id]")
            if stored_rows.count() != 1:
                raise AssertionError(
                    "Outputs view did not retain exactly one in-memory report."
                )
            if "Vytvořené výstupy" not in outputs_view.inner_text():
                raise AssertionError("Outputs view did not leave its empty state.")

            requests_before_reopen = len(report_requests)
            with page.expect_popup() as stored_popup_info:
                stored_rows.first.get_by_role(
                    "button", name="Otevřít report"
                ).click()
            stored_page = stored_popup_info.value
            stored_page.get_by_text("Česká srážková daň", exact=True).wait_for()
            stored_page.close()
            if len(report_requests) != requests_before_reopen:
                raise AssertionError(
                    "Reopening an in-memory output unexpectedly recalculated report."
                )

            if console_errors:
                raise AssertionError(
                    f"Browser console errors: {console_errors!r}"
                )

            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    print("Workspace professional report export and history: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
