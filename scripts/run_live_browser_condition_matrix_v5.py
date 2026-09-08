from __future__ import annotations

import sys
from typing import Any

import run_live_browser_condition_matrix as base
import run_live_browser_condition_matrix_v2 as v2
import run_live_browser_condition_matrix_v4 as v4


def finish_dynamic_questions(page, payload: dict[str, Any]) -> None:
    try:
        v2.finish_dynamic_questions(page, payload)
    except AssertionError as exc:
        if (
            str(exc) == "dynamic questions did not resolve"
            and v4._legitimately_unreachable_after_intake()
        ):
            return
        raise


def install() -> None:
    v4.install()
    base.finish_dynamic_questions = finish_dynamic_questions


def main() -> int:
    install()
    return base.main()


if __name__ == "__main__":
    sys.exit(main())
