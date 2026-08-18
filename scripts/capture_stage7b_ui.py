from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8765
BASE_URL = f"http://{HOST}:{PORT}"


def _wait_for_server(process: subprocess.Popen[bytes]) -> None:
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _answer_first_visible_question(page) -> tuple[str | None, int, int]:
    questions = int(page.locator("#question-count").inner_text())
    visible_questions = page.locator("#questions .question").count()
    if questions < 1 or visible_questions < 1:
        return None, questions, visible_questions

    first_input = page.locator("#questions .question-input").first
    input_path = first_input.get_attribute("data-input-path")
    response_type = first_input.get_attribute("data-response-type")
    if response_type == "date":
        first_input.fill("2025-01-01")
    elif response_type == "boolean":
        first_input.select_option("true")
    elif response_type == "choice":
        first_input.select_option(index=1)
    else:
        first_input.fill("25")

    page.locator("#questions .wizard-save").click()
    page.wait_for_function(
        """([path, count]) => {
            const value = Number(document.querySelector('#question-count').textContent);
            return value < count || !document.querySelector(`[data-input-path="${path}"]`);
        }""",
        arg=[input_path, questions],
    )
    return input_path, questions, visible_questions


def capture(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = output_dir / "stage7b-guided-intake-desktop.png"
    mobile_path = output_dir / "stage7b-guided-intake-mobile.png"
    workspace_path = output_dir / "stage7c-workspace-dashboard.png"
    workspace_result_path = output_dir / "stage7c-workspace-result.png"

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

    questions = 0
    visible_questions = 0
    questions_after_answer = 0

    try:
        _wait_for_server(process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1440, "height": 1100},
                locale="cs-CZ",
            )
            console_errors: list[str] = []
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text)
                    if message.type == "error"
                    else None
                ),
            )

            # Primary client workspace on /ui.
            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")

            boundary = page.locator(".demo-notice .information-only-note")
            if not boundary.is_visible():
                raise AssertionError("Primary workspace information-only notice is missing.")

            boundary_text = boundary.inner_text().lower()
            if "neposkytuje individuální právní ani daňové poradenství" not in boundary_text:
                raise AssertionError("Primary workspace advice boundary is incomplete.")

            for label in ("Přehled", "Plátci", "Příjemci", "Výpočty", "Výstupy", "Zdroje"):
                if not page.get_by_role("button", name=label, exact=True).is_visible():
                    raise AssertionError(f"Primary workspace navigation missing: {label}")

            page.screenshot(path=desktop_path, full_page=True)

            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=mobile_path, full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1100})

            page.get_by_role("button", name="Nový výpočet →").first.click()

            if not page.locator('.flow-step[data-step="1"].active').is_visible():
                raise AssertionError("Workspace step 1 is not active.")

            page.get_by_role("button", name="Pokračovat k příjemci →").click()
            page.get_by_role("button", name="Pokračovat k platbě →").click()

            workspace_form = page.locator("#workspace-payment")

            if not workspace_form.locator('input[name="beneficial_owner"][value="true"]').is_checked():
                raise AssertionError("Beneficial-owner assumption is not available/defaulted.")

            if not workspace_form.locator('input[name="treaty_resident"][value="true"]').is_checked():
                raise AssertionError("Treaty-residence assumption is not available/defaulted.")

            if not workspace_form.locator('input[name="pe_connection"][value="false"]').is_checked():
                raise AssertionError("PE-connection assumption is not available/defaulted.")

            workspace_form.locator('select[name="income_type"]').select_option("dividend")
            workspace_form.locator('input[name="transaction_date"]').fill("2026-08-11")
            workspace_form.locator('input[name="amount"]').fill("100000")
            workspace_form.locator('input[name="ownership_percent"]').fill("25")
            workspace_form.locator('select[name="direct_ownership"]').select_option("true")
            workspace_form.locator('select[name="holding_period_mode"]').select_option("known_date")
            workspace_form.locator('input[name="acquisition_date"]').fill("2024-01-01")

            questions = 0
            visible_questions = 0
            questions_after_answer = 0

            for _ in range(6):
                workspace_form.locator("#workspace-submit").click()
                page.wait_for_timeout(350)

                if page.locator('.flow-step[data-step="4"].active').is_visible():
                    break

                workspace_questions = workspace_form.locator("#workspace-questions")
                questions = workspace_questions.locator(".question-card").count()
                visible_questions = questions

                for item in workspace_questions.locator("select").all():
                    if item.locator("option").count() > 1:
                        item.select_option(index=1)

                for item in workspace_questions.locator('input[type="number"]').all():
                    if not item.input_value():
                        item.fill("25")

                for item in workspace_questions.locator('input[type="date"]').all():
                    if not item.input_value():
                        item.fill("2024-01-01")
            else:
                raise AssertionError("Primary workspace client questions did not converge.")

            page.locator("#workspace-result-status").wait_for(state="visible")

            if page.locator("#workspace-citations .citation-card").count() < 1:
                raise AssertionError("Primary workspace result did not expose legal support.")

            if page.locator("#workspace-notification-deadline").inner_text() == "—":
                raise AssertionError("Primary workspace did not render notification deadline.")

            report_button = page.get_by_role("button", name="Tisk / PDF reportu", exact=True)
            if not report_button.is_visible():
                raise AssertionError("Primary workspace report export action is missing.")

            questions_after_answer = page.locator("#workspace-questions .question-card").count()

            # Workspace: verify the information boundary that remains visible
            # after the old prototype label was intentionally de-emphasised.
            page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
            boundary = page.locator(".demo-notice .information-only-note")
            if not boundary.is_visible():
                raise AssertionError("Workspace information-only notice is missing.")
            boundary_text = boundary.inner_text().lower()
            if "neposkytuje individuální právní ani daňové poradenství" not in boundary_text:
                raise AssertionError("Workspace advice boundary is incomplete.")
            page.screenshot(path=workspace_path, full_page=True)

            page.get_by_role("button", name="Nový výpočet →").first.click()
            page.get_by_role("button", name="Pokračovat k příjemci →").click()
            page.get_by_role("button", name="Pokračovat k platbě →").click()
            workspace_form = page.locator("#workspace-payment")
            workspace_form.locator('select[name="income_type"]').select_option("dividend")
            workspace_form.locator('input[name="transaction_date"]').fill("2026-08-11")
            workspace_form.locator('input[name="amount"]').fill("100000")
            workspace_form.locator('input[name="ownership_percent"]').fill("25")
            workspace_form.locator('select[name="direct_ownership"]').select_option("true")
            workspace_form.locator('select[name="holding_period_mode"]').select_option("known_date")
            workspace_form.locator('input[name="acquisition_date"]').fill("2024-01-01")

            for _ in range(6):
                workspace_form.locator("#workspace-submit").click()
                page.wait_for_timeout(300)
                if page.locator('.flow-step[data-step="4"].active').is_visible():
                    break
                workspace_questions = workspace_form.locator("#workspace-questions")
                for item in workspace_questions.locator("select").all():
                    if item.locator("option").count() > 1:
                        item.select_option(index=1)
                for item in workspace_questions.locator('input[type="number"]').all():
                    item.fill("25")
                for item in workspace_questions.locator('input[type="date"]').all():
                    item.fill("2024-01-01")
            else:
                raise AssertionError("Workspace client questions did not converge.")

            page.locator("#workspace-result-status").wait_for(state="visible")
            if page.locator("#workspace-citations .citation-card").count() < 1:
                raise AssertionError("Workspace result did not expose legal support.")
            if page.locator("#workspace-notification-deadline").inner_text() == "—":
                raise AssertionError("Workspace did not render a notification deadline.")
            page.screenshot(path=workspace_result_path, full_page=True)

            if console_errors:
                raise AssertionError(f"Browser console errors: {console_errors!r}")
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    summary = {
        "schema_version": 2,
        "base_url": "/ui",
        "scenario": "CZ-AT dividend guided intake",
        "analysis_status": "REVIEW_REQUIRED",
        "question_count": questions,
        "initially_visible_questions": visible_questions,
        "question_count_after_answer": questions_after_answer,
        "screenshots": [
            {"name": desktop_path.name, "width": 1440, "sha256": _sha256(desktop_path)},
            {"name": mobile_path.name, "width": 390, "sha256": _sha256(mobile_path)},
            {"name": workspace_path.name, "width": 1440, "sha256": _sha256(workspace_path)},
            {"name": workspace_result_path.name, "width": 1440, "sha256": _sha256(workspace_result_path)},
        ],
    }
    (output_dir / "stage7b-browser-e2e.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    output_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "artifacts" / "stage7b"
    )
    summary = capture(output_dir)
    print(
        "Stage 7B browser E2E: PASS "
        f"({summary['question_count']} questions, "
        f"{summary['question_count_after_answer']} after answer)"
    )
    for screenshot in summary["screenshots"]:
        print(f"{screenshot['name']}: {screenshot['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
