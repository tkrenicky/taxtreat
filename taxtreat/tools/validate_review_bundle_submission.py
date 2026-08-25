from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

APPROVABLE_DECISIONS = frozenset({"approve", "correct"})


def validate_review_bundle_submission(
    review_pack: dict[str, Any],
    *,
    expected_review_bundle_id: str,
) -> dict[str, Any]:
    """Validate human review integrity before any canonical materialization.

    This validator never releases or materializes legal rules. It only reports
    whether the submitted human review is structurally eligible for a later,
    separate promotion step.
    """
    actual_bundle_id = str(review_pack.get("review_bundle_id") or "").strip()
    if not expected_review_bundle_id.startswith("sha256:"):
        raise ValueError("Expected review bundle id must be a sha256 identity")
    if actual_bundle_id != expected_review_bundle_id:
        raise ValueError("Human-review bundle identity does not match expected machine evidence")

    rows = review_pack.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Human-review pack contains no rows")

    results: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        partner = str(row.get("partner_label") or "").strip()
        income_type = str(row.get("income_type") or "").strip()
        blockers: list[str] = []

        if str(row.get("review_bundle_id") or "").strip() != expected_review_bundle_id:
            blockers.append("row_review_bundle_identity_mismatch")
        if row.get("review_ready") is not True or row.get("review_blockers"):
            blockers.append("machine_review_scope_not_ready")

        decision = str(row.get("reviewer_decision") or "").strip().lower()
        if decision not in APPROVABLE_DECISIONS:
            blockers.append("primary_review_not_approved")
        if decision == "correct" and not str(row.get("reviewer_corrected_conclusion") or "").strip():
            blockers.append("corrected_conclusion_missing")
        if decision == "correct" and not list(row.get("reviewer_evidence_references") or []):
            blockers.append("correction_evidence_reference_missing")
        if not str(row.get("reviewer_name") or "").strip():
            blockers.append("reviewer_name_missing")
        if not str(row.get("reviewed_at") or "").strip():
            blockers.append("reviewed_at_missing")
        if str(row.get("independent_approval_status") or "").strip().lower() != "approved":
            blockers.append("independent_approval_missing")

        results.append({
            "row_number": index,
            "partner_label": partner,
            "income_type": income_type,
            "eligible_for_later_canonical_materialization": not blockers,
            "promotion_blockers": blockers,
        })

    eligible = sum(row["eligible_for_later_canonical_materialization"] for row in results)
    return {
        "schema_version": 1,
        "source_country": str(review_pack.get("source_country") or "").strip().upper(),
        "review_bundle_id": actual_bundle_id,
        "status": "review_bundle_promotion_validation_only_not_released",
        "scope_count": len(results),
        "eligible_scope_count": eligible,
        "blocked_scope_count": len(results) - eligible,
        "all_scopes_eligible": eligible == len(results),
        "policy": {
            "validation_does_not_materialize_canonical_rules": True,
            "validation_does_not_release_country": True,
            "review_bundle_identity_must_match": True,
            "primary_review_required": True,
            "independent_approval_required": True,
            "corrections_require_evidence_reference": True,
            "fail_closed": True,
        },
        "rows": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-pack", type=Path, required=True)
    parser.add_argument("--expected-review-bundle-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    pack = json.loads(args.review_pack.read_text(encoding="utf-8"))
    result = validate_review_bundle_submission(
        pack,
        expected_review_bundle_id=args.expected_review_bundle_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "Review bundle validation:",
        result["review_bundle_id"],
        result["eligible_scope_count"],
        "eligible /",
        result["blocked_scope_count"],
        "blocked",
    )


if __name__ == "__main__":
    main()
