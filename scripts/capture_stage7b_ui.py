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

            # Guided client intake: verify the redesigned information-only shell.
            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")
            if not page.get_by_text("Informační nástroj", exact=True).is_visible():
                raise AssertionError("Information-only notice is missing.")
            if not page.get_by_text("Právní stav ke dni 12. 8. 2026", exact=False).is_visible():
                raise AssertionError("Legal-state date is missing.")
            if page.locator(".project-metrics").count():
                raise AssertionError("Marketing metrics leaked into the client intake.")
            if not page.locator("#empty-state").is_visible():
                raise AssertionError("Initial empty result state is missing.")

            page.select_option('select[name="recipient_country"]', "AT")
            page.select_option('select[name="income_type"]', "dividend")
            page.fill('input[name="transaction_date"]', "2026-08-12")
            page.fill('input[name="amount"]', "100000")
            page.select_option('select[name="currency"]', "CZK")
            page.click('#case-form button[type="submit"]')

            result = page.locator("#result")
            result.wait_for(state="visible")
            page.locator("#client-result-layout").wait_for(state="visible")
            if page.locator("#empty-state").is_visible():
                raise AssertionError("Empty state remained visible after calculation.")
            if not page.locator("#hero-outcome").is_visible():
                raise AssertionError("Answer-first result hero is missing.")
            if not page.locator("#legal-basis-content").is_visible():
                raise AssertionError("Live legal-source section is missing.")
            if not page.locator("#deadline-items").is_visible():
                raise AssertionError("Live deadline section is missing.")
            if not page.locator("#documentation-items").is_visible():
                raise AssertionError("Live documentation section is missing.")
            if "individuální daňové" not in page.locator("#hero-explanation").inner_text().lower():
                raise AssertionError("Result advice-boundary wording is missing.")
            if not page.get_by_role("button", name="Zobrazit klientský report").is_visible():
                raise AssertionError("Primary report action is missing.")

            status = page.locator("#status-badge").inner_text()
            if status != "DOPLNIT ÚDAJE":
                raise AssertionError(
                    "Expected localized review status, "
                    f"received {status!r}."
                )

            questions = int(page.locator("#question-count").inner_text())
            visible_questions = page.locator("#questions .question").count()
            if visible_questions != min(questions, 3):
                raise AssertionError(
                    "Guided intake pagination regressed: "
                    f"{visible_questions=} {questions=}."
                )

            page.screenshot(path=desktop_path, full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=mobile_path, full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1100})

            _, _, _ = _answer_first_visible_question(page)
            questions_after_answer = int(page.locator("#question-count").inner_text())
            if questions_after_answer >= questions:
                raise AssertionError(
                    "Supplying a client fact did not reduce the unresolved intake plan."
                )
            if page.locator("#answer-error").is_visible():
                raise AssertionError(page.locator("#answer-error").inner_text())

            page.add_init_script(
                "window.print = () => { window.__taxtreatPrintCalled = true; };"
            )
            with page.expect_popup() as report_popup_info:
                page.locator("#report-button").click()
            report_page = report_popup_info.value
            report_page.wait_for_load_state("domcontentloaded")
            report_page.get_by_role(
                "heading",
                name="Informace k české srážkové dani",
                exact=True,
            ).wait_for()
            report_page.wait_for_function(
                "() => window.__taxtreatPrintCalled === true",
                timeout=5000,
            )
            report_page.close()

            # Workspace: verify the information boundary that remains visible
            # after the old prototype label was intentionally de-emphasised.
            page.goto(f"{BASE_URL}/workspace-demo", wait_until="networkidle")
            boundary = page.locator(".demo-notice .information-only-note")
            if not boundary.is_visible():
                raise AssertionError("Workspace information-only notice is missing.")
            boundary_text = boundary.inner_text().lower()
            if "neposkytuje individuální daňové nebo právní poradenství" not in boundary_text:
                raise AssertionError("Workspace advice boundary is incomplete.")
            if not page.get_by_text("Demo režim", exact=True).is_visible():
                raise AssertionError("Workspace demo-state label is missing.")
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
