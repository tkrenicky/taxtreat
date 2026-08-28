from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8767
BASE_URL = f"http://{HOST}:{PORT}"


def wait_server(process):
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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.set_default_timeout(5000)
            page.goto(f"{BASE_URL}/ui/en", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(700)

            # New payer must save, become active and remain switchable.
            print("checkpoint: open payers", flush=True)
            page.locator('[data-nav="payers"]').click()
            page.locator('[data-create-payer]').first.click()
            payer = page.locator("#payer-form")
            payer.locator('[name="payer_id"]').fill("12345679")
            payer.locator('[name="payer_name"]').fill("QA Payer s.r.o.")
            print("checkpoint: save payer", flush=True)
            payer.locator('[data-save-payer]').click()
            page.wait_for_timeout(250)
            active = page.locator("#active-payer-select")
            assert "QA Payer s.r.o." in active.locator("option").all_text_contents()
            assert active.locator("option:checked").inner_text() == "QA Payer s.r.o."
            print("checkpoint: switch payer", flush=True)
            active.select_option("demo-cz")
            assert active.locator("option:checked").inner_text() == "Demo CZ s.r.o."
            qa_value = active.locator("option", has_text="QA Payer s.r.o.").get_attribute("value")
            active.select_option(qa_value)
            assert active.locator("option:checked").inner_text() == "QA Payer s.r.o."

            # New recipient must save into the working profile.
            print("checkpoint: create recipient", flush=True)
            page.locator('[data-start-flow]').first.click()
            page.locator('.flow-step[data-step="1"] [data-next-step="2"]').click()
            page.locator("[data-show-recipient-form]").click()
            recipient = page.locator("#new-recipient-form")
            recipient.locator('[name="recipient_name"]').fill("QA GmbH")
            recipient.locator('[name="recipient_country"]').select_option("AT")
            recipient.locator('button[type="submit"]').click()
            assert page.locator("#flow-recipient-name").inner_text() == "QA GmbH"

            # Dividend with unresolved exemption facts must still expose the
            # treaty fallback instead of a blank result.
            page.locator('.flow-step[data-step="2"] [data-next-step="3"]').click()
            form = page.locator("#workspace-payment")
            form.locator('select[name="income_type"]').select_option("dividend")
            form.locator('input[name="transaction_date"]').fill("2026-08-11")
            form.locator('input[name="amount"]').fill("100000")
            form.locator('input[name="ownership_percent"]').fill("25")
            form.locator('select[name="direct_ownership"]').select_option("true")
            form.locator('select[name="holding_period_mode"]').select_option("at_least_12_months")
            form.locator('input[name="voting_ownership_percent"]').fill("25")
            # Intentionally leave section19_company_form and
            # section19_taxable_company blank.
            print("checkpoint: submit dividend fallback", flush=True)
            form.locator("#workspace-submit").click()
            page.wait_for_timeout(900)

            result = page.locator('.flow-step[data-step="4"].active')
            assert result.is_visible()
            text = result.inner_text()
            assert "Treaty fallback" in text
            assert "FACTS REQUIRED TO ASSIGN A RULE" not in text
            assert "Additional factual condition requires completion or review." not in text
            assert (
                "Recipient legal form for the exemption" in text
                or "Recipient taxation for the exemption" in text
            )
            assert result.locator("#workspace-tax").inner_text() != "—"

            # Profile state must survive a reload in this browser.
            print("checkpoint: reload persistence", flush=True)
            page.reload(wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(500)
            active = page.locator("#active-payer-select")
            assert "QA Payer s.r.o." in active.locator("option").all_text_contents()

            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    print("Workspace profile and dividend fallback acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
