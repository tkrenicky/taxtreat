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

            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")
            help_link = page.locator('a[href="#napoveda"]').first
            if help_link.count() != 1:
                raise AssertionError("Client methodology link is missing.")
            help_link.click()
            page.wait_for_function(
                "() => window.location.hash === '#napoveda'"
            )
            if not page.locator("#help-title").is_visible():
                raise AssertionError("Client methodology section is not visible.")
            page.goto(f"{BASE_URL}/ui", wait_until="networkidle")
            page.select_option(
                'select[name="recipient_country"]',
                "AT",
            )
            page.select_option('select[name="income_type"]', "dividend")
            page.fill('input[name="transaction_date"]', "2026-08-12")
            page.fill('input[name="amount"]', "100000")
            page.select_option('select[name="currency"]', "CZK")
            page.click('#case-form button[type="submit"]')

            result = page.locator("#result")
            result.wait_for(state="visible")
            status = page.locator("#status-badge").inner_text()
            if status != "DOPLNIT ÚDAJE":
                raise AssertionError(
                    "Expected localized review status, "
                    f"received {status!r}."
                )
            visible_questions = page.locator(
                "#questions .question"
            ).count()
            questions = int(
                page.locator("#question-count").inner_text()
            )
            if visible_questions != min(questions, 3):
                raise AssertionError(
                    "Guided intake pagination regressed: "
                    f"{visible_questions=} {questions=}."
                )
            progress_copy = page.locator(
                "#questions .wizard-progress"
            ).inner_text()
            expected_range = f"Položky 1–{min(questions, 3)}"
            if expected_range not in progress_copy:
                raise AssertionError(
                    f"Unexpected wizard progress: {progress_copy!r}."
                )
            first_prompt = page.locator(
                "#questions .question p"
            ).first.inner_text()
            if not any(
                phrase in first_prompt
                for phrase in (
                    "Od jakého data",
                    "základním kapitálu českého plátce",
                )
            ):
                raise AssertionError(
                    f"Expected Czech intake copy, received {first_prompt!r}."
                )
            if page.locator("#form-error").is_visible():
                raise AssertionError(
                    page.locator("#form-error").inner_text()
                )
            if console_errors:
                raise AssertionError(
                    f"Browser console errors: {console_errors!r}"
                )

            page.screenshot(path=desktop_path, full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=mobile_path, full_page=True)

            first_input = page.locator(
                "#questions .question-input"
            ).first
            first_input_path = first_input.get_attribute("data-input-path")
            response_type = first_input.get_attribute("data-response-type")
            if response_type == "date":
                first_input.fill("2025-01-01")
            elif response_type == "boolean":
                first_input.select_option("true")
            else:
                first_input.fill("25")

            if questions > visible_questions:
                page.locator("#questions .wizard-next").click()
                if "Krok 2" not in page.locator(
                    "#questions .wizard-progress"
                ).inner_text():
                    raise AssertionError(
                        "Wizard did not advance to the second page."
                    )
                page.locator("#questions .wizard-back").click()
                first_input = page.locator(
                    f'[data-input-path="{first_input_path}"]'
                )
                expected_value = (
                    "2025-01-01" if response_type == "date"
                    else "true" if response_type == "boolean"
                    else "25"
                )
                if first_input.input_value() != expected_value:
                    raise AssertionError(
                        "Wizard did not preserve the draft answer."
                    )

            page.locator("#questions .wizard-save").click()
            page.wait_for_function(
                """([path, count]) => {
                    const current = Number(document.querySelector(
                        '#question-count'
                    ).textContent);
                    return current < count || !document.querySelector(
                        `[data-input-path="${path}"]`
                    );
                }""",
                arg=[first_input_path, questions],
            )
            questions_after_answer = int(
                page.locator("#question-count").inner_text()
            )
            if questions_after_answer >= questions:
                raise AssertionError(
                    "Supplying a client fact did not reduce "
                    "the unresolved intake plan."
                )
            if page.locator("#answer-error").is_visible():
                raise AssertionError(
                    page.locator("#answer-error").inner_text()
                )

            documents = page.locator(".documents-panel")
            documents.locator("summary").click()
            if not documents.evaluate("(element) => element.open"):
                raise AssertionError(
                    "Required-document panel did not open."
                )

            page.add_init_script("window.print = () => { window.__taxtreatPrintCalled = true; };")
            with page.expect_popup() as report_popup_info:
                page.locator("#report-button").click()
            report_page = report_popup_info.value
            report_page.wait_for_load_state("domcontentloaded")
            report_page.get_by_role("heading", name="Informace k české srážkové dani", exact=True).wait_for()
            report_page.wait_for_function("() => window.__taxtreatPrintCalled === true", timeout=5000)
            report_page.close()

            page.set_viewport_size({"width": 1440, "height": 1100})
            page.goto(
                f"{BASE_URL}/workspace-demo",
                wait_until="networkidle",
            )
            if not page.get_by_text(
                "Návrh pracovního prostoru",
                exact=True,
            ).is_visible():
                raise AssertionError(
                    "Workspace data-boundary notice is missing."
                )
            page.screenshot(path=workspace_path, full_page=True)
            page.get_by_role(
                "button",
                name="Nový výpočet →",
            ).first.click()
            page.get_by_role(
                "button",
                name="Pokračovat k příjemci →",
            ).click()
            page.get_by_role(
                "button",
                name="Pokračovat k platbě →",
            ).click()
            workspace_form = page.locator("#workspace-payment")
            workspace_form.locator(
                'select[name="income_type"]'
            ).select_option("dividend")
            if workspace_form.locator("#royalty-facts").is_visible():
                raise AssertionError(
                    "Royalty facts leaked into the dividend flow."
                )
            if workspace_form.locator(
                '[data-dividend-step="2"]'
            ).is_visible():
                raise AssertionError(
                    "Dividend questions did not start progressively."
                )
            workspace_form.locator(
                'input[name="transaction_date"]'
            ).fill("2026-08-11")
            workspace_form.locator(
                'input[name="amount"]'
            ).fill("100000")
            workspace_form.locator(
                'input[name="ownership_percent"]'
            ).fill("25")
            if not workspace_form.locator(
                '[data-dividend-step="2"]'
            ).is_visible():
                raise AssertionError(
                    "Second dividend question did not open."
                )
            workspace_form.locator(
                'select[name="direct_ownership"]'
            ).select_option("true")
            if not workspace_form.locator(
                '[data-dividend-step="3"]'
            ).is_visible():
                raise AssertionError(
                    "Holding-period question did not open."
                )
            workspace_form.locator(
                'select[name="holding_period_mode"]'
            ).select_option("known_date")
            workspace_form.locator(
                'input[name="acquisition_date"]'
            ).fill("2024-01-01")
            voting = workspace_form.locator(
                'input[name="voting_ownership_percent"]'
            )
            if not workspace_form.locator(
                '[data-dividend-step="4"]'
            ).is_visible():
                raise AssertionError(
                    "Voting-rights question did not open."
                )
            if voting.input_value() != "25":
                raise AssertionError(
                    "Voting rights were not prefilled from capital share."
                )
            for _ in range(5):
                workspace_form.locator("#workspace-submit").click()
                page.wait_for_timeout(250)
                if page.locator(
                    '.flow-step[data-step="4"].active'
                ).is_visible():
                    break
                workspace_questions = workspace_form.locator(
                    "#workspace-questions"
                )
                for item in workspace_questions.locator("select").all():
                    options = item.locator("option").all()
                    if len(options) > 1:
                        item.select_option(index=1)
                for item in workspace_questions.locator(
                    'input[type="number"]'
                ).all():
                    item.fill("25")
                for item in workspace_questions.locator(
                    'input[type="date"]'
                ).all():
                    item.fill("2024-01-01")
            else:
                raise AssertionError(
                    "Workspace client questions did not converge."
                )
            page.locator("#workspace-result-status").wait_for(
                state="visible"
            )
            workspace_status = page.locator(
                "#workspace-result-status"
            ).inner_text()
            if workspace_status not in {
                "VÝPOČET DOKONČEN",
                "ODBORNÉ OVĚŘENÍ",
            }:
                raise AssertionError(
                    "Workspace did not render the canonical review status: "
                    f"{workspace_status!r}."
                )
            if page.locator("#workspace-actions .action-item").count() < 1:
                raise AssertionError(
                    "Workspace result did not expose actionable next steps."
                )
            citation_cards = page.locator(
                "#workspace-citations .citation-card"
            )
            if citation_cards.count() < 1:
                raise AssertionError(
                    "Workspace result did not expose legal support."
                )
            primary_citation = citation_cards.first
            if not primary_citation.locator("p").inner_text().strip():
                raise AssertionError(
                    "Workspace legal support is missing a readable summary."
                )
            source_url = primary_citation.locator("a").get_attribute("href")
            if not source_url or not source_url.startswith("https://"):
                raise AssertionError(
                    "Workspace legal support is missing an official link."
                )
            if "schválený text" in page.locator(
                "#workspace-citations"
            ).inner_text().lower():
                raise AssertionError(
                    "Workspace incorrectly describes source wording as approved."
                )
            reference_date = page.locator(
                "#workspace-reference-date"
            ).inner_text()
            if "2026" not in reference_date:
                raise AssertionError(
                    "Workspace did not bind the transaction date "
                    "to the statutory calendar."
                )
            notification_deadline = page.locator(
                "#workspace-notification-deadline"
            ).inner_text()
            if notification_deadline == "—":
                raise AssertionError(
                    "Workspace did not render a notification deadline."
                )
            page.screenshot(
                path=workspace_result_path,
                full_page=True,
            )
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    summary = {
        "schema_version": 1,
        "base_url": "/ui",
        "scenario": "CZ-AT dividend guided intake",
        "analysis_status": "REVIEW_REQUIRED",
        "question_count": questions,
        "initially_visible_questions": visible_questions,
        "question_count_after_answer": questions_after_answer,
        "screenshots": [
            {
                "name": desktop_path.name,
                "width": 1440,
                "sha256": _sha256(desktop_path),
            },
            {
                "name": mobile_path.name,
                "width": 390,
                "sha256": _sha256(mobile_path),
            },
            {
                "name": workspace_path.name,
                "width": 1440,
                "sha256": _sha256(workspace_path),
            },
            {
                "name": workspace_result_path.name,
                "width": 1440,
                "sha256": _sha256(workspace_result_path),
            },
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
        print(
            f"{screenshot['name']}: {screenshot['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
