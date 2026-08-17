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


def verify_recipient_catalog_and_entry(page) -> None:
    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
    page.get_by_role("button", name="Příjemci", exact=True).click()
    page.get_by_role("button", name="Přidat příjemce", exact=True).click()
    form = page.locator("#new-recipient-form")
    form.wait_for(state="visible")
    country = form.locator('select[name="recipient_country"]')
    page.wait_for_function(
        "() => document.querySelector('#new-recipient-form select[name=recipient_country]').options.length === 102",
        timeout=5000,
    )
    if country.locator("option").count() != 102:
        raise AssertionError("Recipient form does not expose all 101 jurisdictions.")
    option_values = country.locator("option").evaluate_all("options => options.map(option => option.value)")
    if "KR" not in option_values or "TW" not in option_values:
        raise AssertionError("Recipient catalog must include both Korea and Taiwan.")
    name = form.locator('input[name="recipient_name"]')
    name.fill("Test Korea Co.")
    if name.input_value() != "Test Korea Co.":
        raise AssertionError("Recipient name field is not writable.")
    country.select_option("KR")
    form.get_by_role("button", name="Použít příjemce v této kontrole →").click()
    if page.locator("#flow-recipient-name").inner_text() != "Test Korea Co.":
        raise AssertionError("New recipient was not applied to the workspace.")
    if "undefined" in page.locator("#flow-recipient-meta").inner_text().lower():
        raise AssertionError("Dynamic jurisdiction name was not rendered.")


def finish_workspace_calculation(page) -> None:
    page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
    if page.locator("#flow-recipient-name").inner_text() != "Demo GmbH":
        raise AssertionError("Fresh workspace did not reset the demo recipient.")
    if "Rakousko" not in page.locator("#flow-recipient-meta").inner_text():
        raise AssertionError("Fresh workspace did not reset recipient residence to Austria.")
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
        remaining = form.locator("#workspace-questions").inner_text()
        error_text = form.locator("#workspace-error").inner_text()
        raise AssertionError(
            "Workspace client questions did not converge. "
            f"Remaining questions: {remaining!r}; error: {error_text!r}"
        )

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

            page.route(
                "**/company-registry/ares/27082440",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"source":"ARES","ico":"27082440","name":"Google Czech Republic, s.r.o.","vat_id":"CZ27082440","address":"Stroupežnického 3191/17, 150 00 Praha 5","legal_form":"112","data_box":"amqg4i4","established_at":"2003-10-08"}',
                ),
            )
            page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
            page.get_by_role("button", name="Plátci", exact=True).click()
            page.get_by_role("button", name="Přidat plátce", exact=True).click()
            payer_form = page.locator("#payer-form")
            payer_form.locator('input[name="payer_id"]').fill("27082440")
            payer_form.locator('input[name="payer_name"]').wait_for()
            page.wait_for_function("() => document.querySelector('#payer-form input[name=payer_name]').value.includes('Google Czech')", timeout=5000)
            if payer_form.locator('input[name="payer_address"]').input_value() != "Stroupežnického 3191/17, 150 00 Praha 5":
                raise AssertionError("ARES lookup did not populate payer address.")
            if payer_form.locator('input[name="payer_data_box"]').input_value() != "amqg4i4":
                raise AssertionError("ARES lookup did not populate payer data box.")
            page.get_by_role("button", name="Zrušit", exact=True).last.click()

            verify_recipient_catalog_and_entry(page)
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

            print_button = page.locator('[data-report-action="print"]')
            if print_button.count() != 1:
                raise AssertionError("Workspace PDF report action is missing.")
            if page.locator('[data-report-action="open"]').count() != 0:
                raise AssertionError("Obsolete open-report action is still exposed.")

            requests_before_direct_export = len(report_requests)
            with page.expect_popup() as print_popup_info:
                print_button.click()
            print_page = print_popup_info.value
            print_page.wait_for_load_state("domcontentloaded")
            print_page.get_by_text("Posouzení srážkové daně", exact=True).wait_for()
            print_page.get_by_text("Odůvodnění výsledku", exact=True).wait_for()
            print_page.get_by_text("Právní základ", exact=True).wait_for()
            report_body = print_page.locator("body").inner_text()
            if "TAXTREAT-" in report_body:
                raise AssertionError("PDF report still exposes an internal report identifier.")
            if "Otevřít profesionální report" in report_body or "Withholding tax analysis" in report_body:
                raise AssertionError("PDF report still exposes obsolete/internal-facing wording.")
            if print_page.locator(".legal-source").count() < 1:
                raise AssertionError("PDF report contains no legal sources.")
            print_page.wait_for_function(
                "() => window.__taxtreatPrintCalled === true", timeout=5000
            )
            print_page.close()

            if len(report_requests) < requests_before_direct_export + 1:
                raise AssertionError("PDF export did not request /analysis/report.")

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
                    "button", name="Tisk / PDF"
                ).click()
            stored_page = stored_popup_info.value
            stored_page.get_by_text("Posouzení srážkové daně", exact=True).wait_for()
            stored_page.close()
            if len(report_requests) != requests_before_reopen:
                raise AssertionError(
                    "Reopening an in-memory output unexpectedly recalculated report."
                )

            page.get_by_role(
                "button", name="Kontroly plateb", exact=True
            ).click()
            reviews_view = page.locator('[data-view="reviews"].active')
            reviews_view.wait_for(state="visible")
            review_rows = reviews_view.locator("[data-review-report-id]")
            if review_rows.count() != 1:
                raise AssertionError(
                    "Reviews view did not retain exactly one completed payment review."
                )
            review_text = review_rows.first.inner_text()
            if "Dividendy · AT" not in review_text:
                raise AssertionError(
                    "Completed payment review is missing its transaction summary."
                )
            if "Dokončené kontroly" not in reviews_view.inner_text():
                raise AssertionError("Reviews view did not leave its empty state.")

            review_status = review_rows.first.locator(
                ".review-history-status"
            ).inner_text()
            if review_status not in {"DOKONČENO", "VYŽADUJE DOPLNĚNÍ"}:
                raise AssertionError(
                    f"Unexpected completed-review status: {review_status!r}."
                )

            requests_before_review_open = len(report_requests)
            with page.expect_popup() as review_popup_info:
                review_rows.first.get_by_role(
                    "button", name="Tisk / PDF"
                ).click()
            review_page = review_popup_info.value
            review_page.get_by_text("Česká srážková daň", exact=True).wait_for()
            review_page.close()
            if len(report_requests) != requests_before_review_open:
                raise AssertionError(
                    "Opening a stored review unexpectedly recalculated report."
                )

            page.get_by_role("button", name="Přehled", exact=True).click()
            dashboard = page.locator('[data-view="dashboard"].active')
            dashboard.wait_for(state="visible")
            metrics = dashboard.locator(".dashboard-metrics > article")
            completed_metric = metrics.nth(2)
            attention_metric = metrics.nth(3)
            if completed_metric.locator("span").inner_text() != "Dokončené kontroly":
                raise AssertionError("Dashboard completed-review metric is not data-bound.")
            if completed_metric.locator("strong").inner_text() != "1":
                raise AssertionError("Dashboard completed-review count is incorrect.")
            expected_attention = "1" if review_status == "VYŽADUJE DOPLNĚNÍ" else "0"
            if attention_metric.locator("strong").inner_text() != expected_attention:
                raise AssertionError(
                    "Dashboard attention count does not match stored review status."
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

    print("Workspace professional report, output and review history: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
