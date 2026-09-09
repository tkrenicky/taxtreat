from __future__ import annotations

import json
import sys
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v4 as v4
import run_live_browser_condition_matrix_v5 as v5


# Recipient-type options have locale-specific display labels and, because the
# historical HTML options do not carry explicit values, their values are also
# locale-specific. Select them by the stable semantic option order instead of
# by Czech UI copy so the same browser scenario works in /ui/cs and /ui/en.
RECIPIENT_TYPE_INDEX = {
    "Společnost": 0,
    "Fyzická osoba": 1,
    "Fond": 2,
    "Jiný subjekt": 3,
}


def ensure_recipient_type(page, desired_type: str) -> None:
    if desired_type == v4.CURRENT_RECIPIENT_TYPE:
        return

    page.locator('[data-flow-step="2"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"2\"].active'))"
    )
    page.locator('.flow-step[data-step="2"] [data-edit-recipient]:visible').click()
    page.wait_for_function("() => Boolean(document.querySelector('#recipient-dialog')?.open)")
    dialog = page.locator("#recipient-dialog #recipient-edit-form")
    type_control = dialog.locator('[name="recipient_type"]')
    base.check(type_control.count() == 1, "recipient type control missing")

    option_index = RECIPIENT_TYPE_INDEX.get(desired_type)
    base.check(option_index is not None, f"unknown recipient type: {desired_type!r}")
    option_count = type_control.locator("option").count()
    base.check(
        option_count > option_index,
        f"recipient type option {option_index} missing; found {option_count} options",
    )
    type_control.select_option(index=option_index)

    dialog.locator('button[type="submit"]').click()
    page.wait_for_function("() => !document.querySelector('#recipient-dialog')?.open")
    page.locator('[data-next-step="3"]:visible').click()
    page.wait_for_function(
        "() => Boolean(document.querySelector('.flow-step[data-step=\"3\"].active'))"
    )
    v4.CURRENT_RECIPIENT_TYPE = desired_type


def intake_diagnostic() -> dict[str, Any]:
    if not v4.LAST_INTAKE_RESPONSES:
        return {"response_captured": False}

    body = v4.LAST_INTAKE_RESPONSES[-1]
    analysis = body.get("analysis") or {}
    intake = body.get("intake") or {}
    questions = intake.get("questions") or []
    return {
        "response_captured": True,
        "analysis_status": analysis.get("status"),
        "candidate_rule_id": analysis.get("candidate_rule_id"),
        "selected_rule_id": analysis.get("selected_rule_id"),
        "candidate_rate": analysis.get("candidate_rate"),
        "rate": analysis.get("rate"),
        "missing_facts": analysis.get("missing_facts") or [],
        "failed_conditions": analysis.get("failed_conditions") or [],
        "client_questions": [
            {
                "question_id": question.get("question_id"),
                "input_path": question.get("input_path"),
                "response_type": question.get("response_type"),
            }
            for question in questions
            if question.get("client_answerable")
        ],
        "professional_questions": [
            {
                "question_id": question.get("question_id"),
                "advisor_topic": question.get("advisor_topic"),
            }
            for question in questions
            if not question.get("client_answerable")
        ],
    }


def finish_dynamic_questions(page, payload: dict[str, Any]) -> None:
    for _ in range(30):
        if page.locator('.flow-step[data-step="4"].active').count():
            return
        if page.locator("#workspace-error").is_visible():
            raise AssertionError(
                "workspace error: "
                + page.locator("#workspace-error").inner_text().strip()
            )

        questions = page.locator("#workspace-questions [data-input-path]")
        count = questions.count()
        if count == 0:
            if v4._legitimately_unreachable_after_intake():
                return
            page.wait_for_timeout(20)
            continue

        for index in range(count):
            base.fill_question(questions.nth(index), payload)

        # Wait for the actual intake response instead of racing the async fetch
        # with a fixed sleep. The old loop could submit the same stale question
        # set repeatedly and then diagnose the first response as the last one.
        with page.expect_response(
            lambda response: (
                "/analysis/intake" in response.url
                and response.request.method == "POST"
            ),
            timeout=10_000,
        ):
            page.locator("#workspace-submit").click()

        page.wait_for_timeout(30)
        if v4._legitimately_unreachable_after_intake():
            return

    diagnostic = json.dumps(
        intake_diagnostic(),
        sort_keys=True,
        ensure_ascii=False,
    )
    raise AssertionError(
        f"dynamic questions did not resolve; last_intake={diagnostic}"
    )


def assert_target_reached(
    scenario: dict[str, Any],
    submitted: dict[str, Any],
) -> None:
    try:
        v4.assert_target_reached(scenario, submitted)
    except AssertionError as exc:
        if "unreachable UI fact" not in str(exc):
            raise
        diagnostic = json.dumps(
            intake_diagnostic(),
            sort_keys=True,
            ensure_ascii=False,
        )
        raise AssertionError(f"{exc}; last_intake={diagnostic}") from exc


def install() -> None:
    v5.install()
    v4.ensure_recipient_type = ensure_recipient_type
    base.finish_dynamic_questions = finish_dynamic_questions
    base.assert_target_reached = assert_target_reached


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
