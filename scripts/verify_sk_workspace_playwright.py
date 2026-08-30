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
NAVIGATION_TIMEOUT_MS = 10_000
DOM_READY_TIMEOUT_MS = 10_000
ACTION_TIMEOUT_MS = 5_000


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


def wait_for_workspace_ready(page) -> None:
    page.wait_for_function(
        """() => {
            const selector = document.querySelector("#active-source-country");
            const context = window.TaxTreatWorkspaceSourceCountry;
            return Boolean(
                selector &&
                context &&
                typeof context.getActiveContext === "function" &&
                document.body.dataset.sourceCountry === "CZ"
            );
        }""",
        timeout=DOM_READY_TIMEOUT_MS,
    )


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

    browser = None
    try:
        wait_for_server(server)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            page = browser.new_page()
            page.set_default_timeout(ACTION_TIMEOUT_MS)
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

            page.goto(
                f"{BASE_URL}/ui",
                wait_until="domcontentloaded",
                timeout=NAVIGATION_TIMEOUT_MS,
            )
            wait_for_workspace_ready(page)

            check(
                page,
                "initial CZ source country",
                '() => document.body.dataset.sourceCountry === "CZ"',
            )

            check(
                page,
                "initial CZ currency",
                '() => document.querySelector("#workspace-payment [name=currency]").value === "CZK"',
            )

            check(
                page,
                "initial CZ runtime released",
                '() => window.TaxTreatWorkspaceSourceCountry.getActiveContext().runtimeReleased === true',
            )

            check(
                page,
                "public source-country selector is hidden",
                '() => document.querySelector("#active-source-country").closest("label").hidden === true',
            )

            check(
                page,
                "SK is not publicly selectable",
                '() => ![...document.querySelectorAll("#active-source-country option")].some(o => o.value === "SK")',
            )

            check(
                page,
                "public source-country context exposes CZ only",
                '() => Object.keys(window.TaxTreatSourceCountries.countries).length === 1 && Object.keys(window.TaxTreatSourceCountries.countries)[0] === "CZ"',
            )

            check(
                page,
                "unsupported SK public context fails closed",
                '''() => {
                    try {
                        window.TaxTreatSourceCountries.get("SK");
                        return false;
                    } catch (error) {
                        return String(error).includes("Unsupported public source country: SK");
                    }
                }''',
            )

            check(
                page,
                "public source country remains CZ",
                '() => document.body.dataset.sourceCountry === "CZ"',
            )

            check(
                page,
                "public currency remains CZK",
                '() => document.querySelector("#workspace-payment [name=currency]").value === "CZK"',
            )

        print("BROWSER_SMOKE_OK")
        return 0

    except Exception as exc:
        print(f"BROWSER_SMOKE_FAILED: {exc}")
        if server_log.exists():
            print(server_log.read_text(encoding="utf-8", errors="replace"))
        return 1

    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass

        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
