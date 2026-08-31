from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8766
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


def body_text(page) -> str:
    return page.locator("body").inner_text()


def main() -> int:
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_server(process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            page.goto(f"{BASE_URL}/ui/en", wait_until="networkidle")
            page.wait_for_timeout(700)

            text = body_text(page)
            for forbidden in (
                "PRACOVNÍ PROSTOR",
                "Platby, příjemci a informace navázané na zadané údaje.",
                "Úkoly",
                "Doklad k případnému smluvnímu nároku není evidován",
            ):
                assert forbidden not in text, forbidden
            assert "WORKSPACE" in text
            assert "Tasks" in text

            page.locator("[data-start-flow]").first.click()
            page.locator('.flow-step[data-step="1"] [data-next-step="2"]').click()
            page.locator('.flow-step[data-step="2"] [data-next-step="3"]').click()
            page.wait_for_timeout(500)

            form = page.locator("#workspace-payment")
            form.locator('select[name="income_type"]').select_option("dividend")
            form.locator('input[name="transaction_date"]').fill("2026-08-11")
            form.locator('input[name="amount"]').fill("10000000")
            form.locator('input[name="ownership_percent"]').fill("25")
            form.locator('select[name="direct_ownership"]').select_option("true")
            form.locator('select[name="holding_period_mode"]').select_option("known_date")
            form.locator('input[name="acquisition_date"]').fill("2024-01-01")
            treaty_resident_yes = form.locator('input[name="treaty_resident"][value="true"]')
            if not treaty_resident_yes.is_checked():
                treaty_resident_yes.evaluate(
                    "el => { el.checked = true; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }"
                )
            form.locator('input[name="voting_ownership_percent"]').fill("25")

            assert form.locator('input[name="ownership_percent"]').get_attribute("placeholder") == "e.g. 25"

            q2 = page.locator('.fact-question[data-dividend-step="2"] > span')
            q3 = page.locator('.fact-question[data-dividend-step="3"] > span')
            page.wait_for_timeout(100)
            q2_size = q2.evaluate("el => getComputedStyle(el).fontSize")
            q3_size = q3.evaluate("el => getComputedStyle(el).fontSize")
            assert q2_size == q3_size, (q2_size, q3_size)

            for name in ("section19_company_form", "section19_taxable_company"):
                select = form.locator(f'select[name="{name}"]')
                if select.count():
                    select.select_option("true")

            for _ in range(8):
                form.locator("#workspace-submit").click()
                page.wait_for_timeout(400)
                if page.locator('.flow-step[data-step="4"].active').is_visible():
                    break
                questions = form.locator("#workspace-questions")
                for item in questions.locator("select").all():
                    if item.locator("option").count() > 1 and not item.input_value():
                        item.select_option(index=1)
                for item in questions.locator('input[type="number"]').all():
                    if not item.input_value():
                        item.fill("25")
                for item in questions.locator('input[type="date"]').all():
                    if not item.input_value():
                        item.fill("2024-01-01")
            else:
                raise AssertionError("result did not converge")

            page.wait_for_timeout(900)
            result = page.locator('.flow-step[data-step="4"].active')
            result_text = result.inner_text()
            for forbidden in (
                "VÝPOČET DOKONČEN",
                "Česká daň k odvodu",
                "Daň se neodvádí",
                "VÝCHOZÍ VNITROSTÁTNÍ PRAVIDLO",
                "POUŽITÉ SMLUVNÍ PRAVIDLO",
                "SEKUNDÁRNÍ SMLUVNÍ OCHRANA",
                "Otevřít zdroj",
                "Znění použitého ustanovení",
            ):
                assert forbidden not in result_text, forbidden

            assert "Dividends" in result_text
            assert "All facts required for the calculation are entered" not in result_text
            assert "Potential domestic exemption" not in result_text
            assert "of the tax base" not in result_text
            assert "Additional factual condition requires completion or review." not in result_text

            if "Exemption assessed" in result_text or "Domestic exemption under the Czech Income Taxes Act" in result_text:
                applied_text = result.locator(".reason").inner_text()
                assert "Czech Income Taxes Act" in applied_text
                assert "Under Article 10" not in applied_text
                assert "SECONDARY TREATY PROTECTION" in result_text

            treaty_blocks = result.locator(".citation-card blockquote")
            if treaty_blocks.count():
                assert max(len(treaty_blocks.nth(i).inner_text().strip()) for i in range(treaty_blocks.count())) > 80

            cs = browser.new_page(viewport={"width": 1440, "height": 1100})
            cs.goto(f"{BASE_URL}/ui/cs", wait_until="networkidle")
            cs_text = body_text(cs)
            assert "Přehled" in cs_text
            assert "Plátci" in cs_text
            assert "WORKSPACE" not in cs_text
            cs.close()

            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    print("Manual QA bilingual UI acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
