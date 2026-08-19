from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import scripts.build_sk_claude_review_bundle as base_bundle


ROOT = Path(__file__).resolve().parents[1]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
BROWSER_LOG = ROOT / "artifacts" / "sk_workspace_browser_smoke.log"
PASS2_BRIEF = SK_DIR / "CLAUDE_ADVERSARIAL_REVIEW_PASS2.md"
PASS1_SUMMARY = SK_DIR / "CLAUDE_PASS1_FINDINGS_SUMMARY.md"


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def _tracked_files() -> list[Path]:
    return [ROOT / line for line in _git("ls-files").splitlines() if line]


def _require_inputs() -> None:
    base_bundle._require_review_inputs()

    for path in (PASS2_BRIEF, PASS1_SUMMARY, BROWSER_LOG):
        if not path.is_file():
            raise RuntimeError(f"Pass-2 Claude review input missing: {path.relative_to(ROOT)}")

    browser_log = BROWSER_LOG.read_text(encoding="utf-8", errors="replace")
    if "BROWSER_SMOKE_OK" not in browser_log:
        raise RuntimeError("Pass-2 Claude review requires a successful BROWSER_SMOKE_OK log.")

    matrix = json.loads(
        (SK_DIR / "prerelease_decision_matrix_summary.json").read_text(
            encoding="utf-8"
        )
    )
    if matrix.get("foreign_runtime_dependency_scopes") != 0:
        raise RuntimeError("Pass-2 bundle requires zero foreign runtime dependency scopes.")
    if matrix.get("czech_runtime_fallback_scopes") != 0:
        raise RuntimeError("Pass-2 bundle requires zero Czech runtime fallback scopes.")


def build_bundle() -> Path:
    _require_inputs()

    branch = _git("branch", "--show-current")
    if branch != "feat/sk-review-ready-20260819":
        raise RuntimeError(
            "Build pass-2 bundle from feat/sk-review-ready-20260819; "
            f"current branch is {branch!r}."
        )

    head = _git("rev-parse", "HEAD")
    base = _git("rev-parse", "main")
    merge_base = _git("merge-base", "main", "HEAD")
    short = head[:12]
    output = ROOT / f"taxtreat-sk-claude-review-pass2-{short}.zip"

    metadata = {
        "schema_version": 1,
        "review_pass": 2,
        "repository": "tkrenicky/taxtreat",
        "base_ref": "main",
        "head_ref": branch,
        "base_sha": base,
        "merge_base_sha": merge_base,
        "head_sha": head,
        "review_brief": PASS2_BRIEF.relative_to(ROOT).as_posix(),
        "pass1_findings_summary": PASS1_SUMMARY.relative_to(ROOT).as_posix(),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "browser_smoke_log": BROWSER_LOG.relative_to(ROOT).as_posix(),
        "generated_evidence_included": [
            path.relative_to(ROOT).as_posix()
            for path in base_bundle.REQUIRED_GENERATED_ARTIFACTS
        ],
    }
    patch = subprocess.check_output(
        ["git", "diff", "--binary", "main...HEAD"],
        cwd=ROOT,
    )
    status = _git("status", "--short")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _tracked_files():
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        for path in base_bundle.REQUIRED_GENERATED_ARTIFACTS:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(BROWSER_LOG, BROWSER_LOG.relative_to(ROOT).as_posix())
        archive.writestr(
            "CLAUDE_REVIEW_PASS2_METADATA.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        archive.writestr("MAIN_TO_SK_BRANCH_PASS2.patch", patch)
        archive.writestr("LOCAL_GIT_STATUS_PASS2.txt", status + "\n")

    return output


def main() -> None:
    output = build_bundle()
    print(output)


if __name__ == "__main__":
    main()
