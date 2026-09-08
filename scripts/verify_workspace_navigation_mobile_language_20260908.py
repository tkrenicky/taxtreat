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

            page.wait_for_selector('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]', state="visible")
            page.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]').click()
            page.wait_for_function("() => document.documentElement.lang === 'en'")
            assert page.locator('.flow-step[data-step="3"]').evaluate("el => el.classList.contains('active')")
            assert page.evaluate("localStorage.getItem('taxtreat-ui-language')") == "en"

            page.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="cs"]').click()
            page.wait_for_function("() => document.documentElement.lang === 'cs'")
            assert page.locator('.flow-step[data-step="3"]').evaluate("el => el.classList.contains('active')")
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

            mobile.wait_for_selector('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]', state="visible")
            mobile.locator('#taxtreat-language-controls .tt-lang-mini button[data-lang="en"]').click()
            mobile.wait_for_function("() => document.documentElement.lang === 'en'")
            assert mobile.locator('.flow-step[data-step="3"]').evaluate("el => el.classList.contains('active')")
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
