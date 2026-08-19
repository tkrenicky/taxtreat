from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
OUT_DIR = ROOT / "artifacts"

REQUIRED_GENERATED_ARTIFACTS = (
    SK_DIR / "domestic_review_readiness.json",
    SK_DIR / "domestic_review_readiness_summary.json",
    SK_DIR / "machine_ingestion_run_summary.json",
    SK_DIR / "mli_instrument_chain_reconciliation.json",
    SK_DIR / "mli_instrument_chain_reconciliation_summary.json",
    SK_DIR / "mli_notice_machine_extraction.json",
    SK_DIR / "mli_notice_machine_extraction_summary.json",
    SK_DIR / "mli_notice_review_queue.json",
    SK_DIR / "mli_notice_review_queue_summary.json",
    SK_DIR / "pre_review_readiness.json",
    SK_DIR / "prerelease_decision_matrix_summary.json",
    SK_DIR / "prerelease_runtime_manifest.json",
    SK_DIR / "prerelease_runtime_manifest_summary.json",
    SK_DIR / "treaty_article_machine_extraction.json",
    SK_DIR / "treaty_article_machine_extraction_summary.json",
    SK_DIR / "treaty_semantic_candidates.json",
    SK_DIR / "treaty_semantic_candidates_summary.json",
    SK_DIR / "treaty_source_review_queue.json",
    SK_DIR / "treaty_source_review_queue_summary.json",
)


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def _tracked_files() -> list[Path]:
    return [ROOT / line for line in _git("ls-files").splitlines() if line]


def _require_review_inputs() -> None:
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in REQUIRED_GENERATED_ARTIFACTS
        if not path.is_file()
    ]
    if missing:
        raise RuntimeError(
            "Claude review bundle requires generated SK evidence. Missing: "
            + ", ".join(missing)
            + ". Run the established SK machine/offline preparation first."
        )

    readiness = json.loads(
        (SK_DIR / "pre_review_readiness.json").read_text(encoding="utf-8")
    )
    matrix = json.loads(
        (SK_DIR / "prerelease_decision_matrix_summary.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (SK_DIR / "prerelease_runtime_manifest_summary.json").read_text(
            encoding="utf-8"
        )
    )

    expected = {
        "scope_count": 225,
        "evaluated_scopes": 225,
        "review_required_scopes": 225,
        "final_rate_scopes": 0,
        "czech_runtime_fallback_scopes": 0,
        "production_released_scopes": 0,
    }
    for key, value in expected.items():
        if matrix.get(key) != value:
            raise RuntimeError(
                f"Decision matrix invariant {key} expected {value!r}, "
                f"got {matrix.get(key)!r}."
            )

    if manifest.get("scope_count") != 225:
        raise RuntimeError("Prerelease runtime manifest must contain 225 scopes.")
    if readiness.get("human_review", {}).get("reviewed_scopes") != 0:
        raise RuntimeError("Claude pre-review bundle requires human review to remain 0/225.")
    if readiness.get("runtime", {}).get("released") is not False:
        raise RuntimeError("Claude pre-review bundle requires SK runtime to remain unreleased.")


def build_bundle() -> Path:
    _require_review_inputs()

    branch = _git("branch", "--show-current")
    if branch != "feat/sk-review-ready-20260819":
        raise RuntimeError(
            "Build the Claude review bundle from feat/sk-review-ready-20260819; "
            f"current branch is {branch!r}."
        )

    head = _git("rev-parse", "HEAD")
    base = _git("rev-parse", "main")
    merge_base = _git("merge-base", "main", "HEAD")
    short = head[:12]
    OUT_DIR.mkdir(exist_ok=True)
    output = OUT_DIR / f"taxtreat-sk-claude-review-{short}.zip"

    tracked = _tracked_files()
    metadata = {
        "schema_version": 1,
        "repository": "tkrenicky/taxtreat",
        "base_ref": "main",
        "head_ref": branch,
        "base_sha": base,
        "merge_base_sha": merge_base,
        "head_sha": head,
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "generated_evidence_included": [
            path.relative_to(ROOT).as_posix()
            for path in REQUIRED_GENERATED_ARTIFACTS
        ],
        "review_brief": "data/legal_reviews/sk_outbound/CLAUDE_ADVERSARIAL_REVIEW.md",
        "review_scope": "data/legal_reviews/sk_outbound/claude_review_scope.json",
    }
    patch = subprocess.check_output(
        ["git", "diff", "--binary", "main...HEAD"],
        cwd=ROOT,
    )
    status = _git("status", "--short")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in tracked:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        for path in REQUIRED_GENERATED_ARTIFACTS:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr(
            "CLAUDE_REVIEW_BUNDLE_METADATA.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        archive.writestr("MAIN_TO_SK_BRANCH.patch", patch)
        archive.writestr("LOCAL_GIT_STATUS.txt", status + "\n")

    return output


def main() -> None:
    output = build_bundle()
    print(output.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
