from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_live_browser_condition_matrix_v4 as matrix_v4  # noqa: E402


def _set_last_response(*, status: str, client: int, professional: int) -> None:
    questions = [
        {"question_id": f"client-{index}", "client_answerable": True}
        for index in range(client)
    ] + [
        {"question_id": f"professional-{index}", "client_answerable": False}
        for index in range(professional)
    ]
    matrix_v4.LAST_INTAKE_RESPONSES[:] = [
        {
            "analysis": {"status": status},
            "intake": {"questions": questions},
        }
    ]


def test_review_required_without_client_questions_is_a_browser_boundary():
    _set_last_response(status="REVIEW_REQUIRED", client=0, professional=0)
    assert matrix_v4._legitimately_unreachable_after_intake()


def test_review_required_never_hides_remaining_client_questions():
    _set_last_response(status="REVIEW_REQUIRED", client=1, professional=1)
    assert not matrix_v4._legitimately_unreachable_after_intake()


def test_final_result_is_a_browser_boundary():
    _set_last_response(status="FINAL", client=0, professional=0)
    assert matrix_v4._legitimately_unreachable_after_intake()
