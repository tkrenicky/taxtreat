from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.services.sk_prerelease_decision import (
    evaluate_sk_prerelease_candidate,
)


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
MANIFEST_PATH = SK_DIR / "prerelease_runtime_manifest.json"
SUMMARY_PATH = SK_DIR / "prerelease_decision_matrix_summary.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_matrix(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = manifest.get("scopes", [])
    if manifest.get("source_country") != "SK":
        raise ValueError("Decision matrix validator requires an SK manifest.")
    if len(rows) != 225:
        raise ValueError("Decision matrix validator requires exactly 225 SK scopes.")

    results = [
        evaluate_sk_prerelease_candidate(
            recipient_country=row["recipient_country"],
            income_type=row["income_type"],
            facts={},
            manifest=manifest,
        )
        for row in rows
    ]

    if any(result.status == "OUT_OF_SCOPE" for result in results):
        raise ValueError("A registered SK runtime scope evaluated as OUT_OF_SCOPE.")
    if any(result.final_rate_percent is not None for result in results):
        raise ValueError("Prerelease matrix emitted a final rate.")
    if any(result.czech_runtime_fallback_used for result in results):
        raise ValueError("Prerelease matrix used a Czech runtime fallback.")
    if any(result.runtime_released for result in results):
        raise ValueError("Prerelease matrix released an SK runtime scope.")
    if any(not result.requires_review for result in results):
        raise ValueError("Prerelease matrix contains a scope not requiring review.")

    return {
        "schema_version": 1,
        "dataset_release": "sk-prerelease-decision-matrix-2026-08-19.1",
        "source_country": "SK",
        "scope_count": 225,
        "evaluated_scopes": len(results),
        "review_required_scopes": sum(
            result.status == "REVIEW_REQUIRED" for result in results
        ),
        "final_rate_scopes": sum(
            result.final_rate_percent is not None for result in results
        ),
        "czech_runtime_fallback_scopes": sum(
            result.czech_runtime_fallback_used for result in results
        ),
        "production_released_scopes": sum(
            result.runtime_released for result in results
        ),
        "scopes_blocked_by_cooperating_state_list": sum(
            "official_2026_cooperating_state_list_body_not_ingested"
            in result.blockers
            for result in results
        ),
        "fail_closed": True,
    }


def main() -> None:
    summary = validate_matrix(_load(MANIFEST_PATH))
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
