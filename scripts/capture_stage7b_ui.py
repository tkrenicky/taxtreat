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
            page.select_option(
                'select[name="recipient_country"]',
                "AT",
            )
            page.select_option('select[name="income_type"]', "dividend")
            page.fill('input[name="transaction_date"]', "2026-08-12")
            page.fill('input[name="amount"]', "100000.55")
            page.select_option('select[name="currency"]', "CZK")
            page.click('#case-form button[type="submit"]')

            result = page.locator("#result")
            result.wait_for(state="visible")
            status = page.locator("#status-badge").inner_text()
            if status != "REVIEW_REQUIRED":
                raise AssertionError(
                    f"Expected REVIEW_REQUIRED, received {status!r}."
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
            if "Otázky 1–3" not in progress_copy:
                raise AssertionError(
                    f"Unexpected wizard progress: {progress_copy!r}."
                )
            first_prompt = page.locator(
                "#questions .question p"
            ).first.inner_text()
            if "skutečným vlastníkem" not in first_prompt:
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

            beneficial_owner = page.locator(
                '[data-input-path="facts.beneficial_owner"]'
            )
            beneficial_owner.select_option("true")

            if questions > visible_questions:
                page.locator("#questions .wizard-next").click()
                if "Krok 2" not in page.locator(
                    "#questions .wizard-progress"
                ).inner_text():
                    raise AssertionError(
                        "Wizard did not advance to the second page."
                    )
                page.locator("#questions .wizard-back").click()
                beneficial_owner = page.locator(
                    '[data-input-path="facts.beneficial_owner"]'
                )
                if beneficial_owner.input_value() != "true":
                    raise AssertionError(
                        "Wizard did not preserve the draft answer."
                    )

            page.locator("#questions .wizard-save").click()
            page.wait_for_function(
                """() => !document.querySelector(
                    '[data-input-path="facts.beneficial_owner"]'
                )"""
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
