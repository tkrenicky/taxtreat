from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
VISIBLE_WORKSPACE_ROOT = Path("/workspaces/taxtreat")
BROWSER_LOG = ROOT / "artifacts" / "sk_workspace_browser_smoke.log"
BRIEF = SK_DIR / "CLAUDE_ADVERSARIAL_REVIEW_PASS2_FOLLOWUP.md"
PASS2_SUMMARY = SK_DIR / "CLAUDE_PASS2_PARTIAL_FINDINGS_SUMMARY.md"

sys.path.insert(0, str(ROOT))
from scripts.build_sk_claude_review_bundle import REQUIRED_GENERATED_ARTIFACTS  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _tracked_files() -> list[Path]:
    return [ROOT / line for line in _git("ls-files").splitlines() if line]


def _require_inputs() -> None:
    if not VISIBLE_WORKSPACE_ROOT.is_dir():
        raise RuntimeError(
            "Visible workspace root /workspaces/taxtreat is missing; refusing to place transfer ZIP elsewhere."
        )
    if _git("branch", "--show-current") != "feat/sk-review-ready-20260819":
        raise RuntimeError("Build the follow-up bundle from feat/sk-review-ready-20260819.")

    main_status = _git("status", "--short", "--", "app/main.py")
    if main_status:
        raise RuntimeError(
            "app/main.py has uncommitted changes. Commit the validated runtime integration before bundling."
        )

    for path in (BRIEF, PASS2_SUMMARY, BROWSER_LOG, *REQUIRED_GENERATED_ARTIFACTS):
        if not path.is_file():
            raise RuntimeError(f"Required follow-up review input missing: {path}")

    browser_log = BROWSER_LOG.read_text(encoding="utf-8", errors="replace")
    if "BROWSER_SMOKE_OK" not in browser_log:
        raise RuntimeError("Follow-up bundle requires BROWSER_SMOKE_OK.")

    matrix = json.loads(
        (SK_DIR / "prerelease_decision_matrix_summary.json").read_text(encoding="utf-8")
    )
    expected = {
        "scope_count": 225,
        "evaluated_scopes": 225,
        "review_required_scopes": 225,
        "final_rate_scopes": 0,
        "czech_runtime_fallback_scopes": 0,
        "foreign_runtime_dependency_scopes": 0,
        "production_released_scopes": 0,
    }
    for key, value in expected.items():
        if matrix.get(key) != value:
            raise RuntimeError(
                f"Decision matrix invariant {key} expected {value!r}, got {matrix.get(key)!r}."
            )

    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    required_main_markers = (
        "return require_source_country_analysis_release(source)",
        "source_country_runtime_dataset_version(",
        "build_source_country_withholding_tax_calculation(",
        "build_source_country_withholding_compliance_schedule(",
    )
    missing = [marker for marker in required_main_markers if marker not in main]
    if missing:
        raise RuntimeError("Validated app/main.py integration is incomplete: " + ", ".join(missing))
    if "SOURCE_COUNTRY_RELEASE_GATE_MISSING" in main:
        raise RuntimeError("Obsolete non-CZ fallthrough marker remains in app/main.py.")


def build_bundle() -> Path:
    _require_inputs()

    head = _git("rev-parse", "HEAD")
    base = _git("rev-parse", "main")
    merge_base = _git("merge-base", "main", "HEAD")
    short = head[:12]
    output = VISIBLE_WORKSPACE_ROOT / f"taxtreat-sk-claude-review-pass2-followup-{short}.zip"

    metadata = {
        "schema_version": 1,
        "review_pass": "2-followup",
        "repository": "tkrenicky/taxtreat",
        "base_ref": "main",
        "head_ref": "feat/sk-review-ready-20260819",
        "base_sha": base,
        "merge_base_sha": merge_base,
        "head_sha": head,
        "review_brief": BRIEF.relative_to(ROOT).as_posix(),
        "pass2_partial_findings": PASS2_SUMMARY.relative_to(ROOT).as_posix(),
        "browser_smoke_log": BROWSER_LOG.relative_to(ROOT).as_posix(),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "transfer_output_directory": str(VISIBLE_WORKSPACE_ROOT),
        "generated_evidence_included": [
            path.relative_to(ROOT).as_posix() for path in REQUIRED_GENERATED_ARTIFACTS
        ],
    }
    patch = subprocess.check_output(
        ["git", "diff", "--binary", "main...HEAD"], cwd=ROOT
    )
    status = _git("status", "--short")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _tracked_files():
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        for path in REQUIRED_GENERATED_ARTIFACTS:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(BROWSER_LOG, BROWSER_LOG.relative_to(ROOT).as_posix())
        archive.writestr(
            "CLAUDE_REVIEW_PASS2_FOLLOWUP_METADATA.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        archive.writestr("MAIN_TO_SK_BRANCH_PASS2_FOLLOWUP.patch", patch)
        archive.writestr("LOCAL_GIT_STATUS_PASS2_FOLLOWUP.txt", status + "\n")

    return output


def main() -> None:
    print(build_bundle())


if __name__ == "__main__":
    main()
