from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from fastapi import HTTPException

from app.main import AnalysisPayload, analyze
from taxtreat.services.acceptance import (
    load_acceptance_fixture,
    render_acceptance_html,
    run_acceptance_suite,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "data/acceptance/stage7a_pilot.json"


def execute(request: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]:
    try:
        return 200, analyze(AnalysisPayload(**request))
    except HTTPException as exc:
        return exc.status_code, {"detail": exc.detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    fixture = load_acceptance_fixture(args.fixture)
    summary = run_acceptance_suite(fixture, execute)

    print(
        f"Stage 7A acceptance: {summary['passed']}/"
        f"{summary['case_count']} passed"
    )
    print(f"Acceptance SHA-256: {summary['acceptance_sha256']}")

    for result in summary["results"]:
        state = "PASS" if result["passed"] else "FAIL"
        print(f"{state} {result['case_id']}")
        for error in result["errors"]:
            print(f"  - {error}")

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "stage7a_acceptance.json").write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "stage7a_acceptance.html").write_text(
            render_acceptance_html(summary),
            encoding="utf-8",
        )

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
