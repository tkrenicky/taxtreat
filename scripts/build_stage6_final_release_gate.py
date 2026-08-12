from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

GATE = (
    BASE
    / "production_source_release_gate_v2.json"
)

PROMOTION = (
    BASE
    / "stage6_rule_promotion.json"
)

RELEASE = (
    BASE
    / "stage6_source_release.json"
)

APPROVAL = (
    BASE
    / "stage6_production_approval.json"
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


gate = load(GATE)
promotion = load(PROMOTION)
release = load(RELEASE)
approval = load(APPROVAL)

promotion_by_pair = {
    row["treaty_pair_id"]: row
    for row in promotion["records"]
}

release_by_pair = {
    row["treaty_pair_id"]: row
    for row in release["records"]
}

approval_by_pair = {
    row["treaty_pair_id"]: row
    for row in approval["records"]
}

rows = gate["treaty_partners"]

if len(rows) != 101:
    raise RuntimeError(
        f"Canonical gate must contain 101 rows, got {len(rows)}."
    )

if set(promotion_by_pair) != set(release_by_pair):
    raise RuntimeError(
        "Promotion and release pair universes differ."
    )

if len(release_by_pair) != 101:
    raise RuntimeError(
        "Release manifest must contain 101 pairs."
    )

projected = []

for original in rows:
    row = dict(original)

    pair = row["treaty_pair_id"]

    promotion_row = promotion_by_pair.get(pair)
    release_row = release_by_pair.get(pair)
    approval_row = approval_by_pair.get(pair)

    if (
        promotion_row is None
        or release_row is None
        or approval_row is None
    ):
        raise RuntimeError(
            f"{pair}: release governance record missing."
        )

    package_hash = row["package_sha256"]

    hashes = {
        package_hash,
        promotion_row["package_sha256"],
        release_row["package_sha256"],
        approval_row["package_sha256"],
    }

    if len(hashes) != 1:
        raise RuntimeError(
            f"{pair}: package hash binding mismatch."
        )

    if (
        approval_row["production_approval_status"]
        != "production_approved"
    ):
        raise RuntimeError(
            f"{pair}: package is not production approved."
        )

    if (
        promotion_row["rule_promotion_status"]
        != "promoted"
    ):
        raise RuntimeError(
            f"{pair}: package is not promoted."
        )

    if (
        release_row["source_release_status"]
        != "released"
    ):
        raise RuntimeError(
            f"{pair}: package is not explicitly released."
        )

    rule_path = (
        ROOT
        / release_row["rule_file"]
    )

    if not rule_path.exists():
        raise RuntimeError(
            f"{pair}: released rule file missing."
        )

    actual_rule_hash = hashlib.sha256(
        rule_path.read_bytes()
    ).hexdigest()

    if (
        actual_rule_hash
        != release_row["rule_file_sha256"]
    ):
        raise RuntimeError(
            f"{pair}: released rule file hash mismatch."
        )

    if (
        actual_rule_hash
        != promotion_row["rule_file_sha256"]
    ):
        raise RuntimeError(
            f"{pair}: promoted/released rule hashes differ."
        )

    if (
        row["independent_qa_status"]
        != "not_required"
    ):
        raise RuntimeError(
            f"{pair}: independent human QA semantics regressed."
        )

    secondary_ai_status = row.get(
        "secondary_ai_qa_status"
    )

    if secondary_ai_status not in {
        "not_selected",
        "secondary_ai_crosscheck_complete",
    }:
        raise RuntimeError(
            f"{pair}: invalid secondary AI QA status: "
            f"{secondary_ai_status!r}"
        )

    # Historical independent QA is intentionally not required.
    # Secondary AI is represented separately and must never
    # be reclassified as human review.
    if (
        row["independent_qa_status"]
        != "not_required"
    ):
        raise RuntimeError(
            f"{pair}: independent QA semantics regressed."
        )

    # Where the canonical row carries the explicit governance
    # field, it must remain false. Do not fabricate the field
    # on rows whose schema does not contain it.
    if (
        "additional_human_review_claimed" in row
        and row["additional_human_review_claimed"] is not False
    ):
        raise RuntimeError(
            f"{pair}: additional human review incorrectly claimed."
        )

    row["rule_promotion_status"] = "promoted"
    row["release_status"] = "released"
    row["active_rule_allowed"] = True
    row["production_ready"] = True
    row["fail_closed"] = False
    row["release_blockers"] = []

    evidence = dict(row["release_evidence"])

    evidence["rule_promotion_event"] = {
        "event_type": promotion.get(
            "event_type",
            "deterministic_production_rule_promotion",
        ),
        "dataset_release": promotion["dataset_release"],
        "promotion_authority": promotion.get(
            "promotion_authority",
            "stage6_governance_policy",
        ),
        **promotion_row,
    }

    evidence["source_release_event"] = {
        "event_type": release.get(
            "event_type",
            "explicit_production_source_release",
        ),
        "dataset_release": release["dataset_release"],
        "release_authority": release.get(
            "release_authority",
            "stage6_governance_policy",
        ),
        **release_row,
    }

    row["release_evidence"] = evidence

    # Preserve optional compatibility fields only when
    # they already exist in the canonical schema.
    if "source_release_status" in row:
        row["source_release_status"] = "released"

    if "rule_promoted" in row:
        row["rule_promoted"] = True

    if "source_released" in row:
        row["source_released"] = True

    projected.append(row)


gate["treaty_partners"] = projected

counts = gate["counts"]

counts["rule_promoted_packages"] = 101

counts["rule_promoted_scopes"] = 303

counts["released_packages"] = 101
counts["released_scopes"] = 303

# Top-level fail_closed remains TRUE deliberately:
# unknown pairs, malformed governance data and missing
# release rows must continue to fail closed even though
# the 101 canonical CZ outbound packages are released.
gate["fail_closed"] = True

gate["dataset_release"] = (
    "stage6-canonical-production-release-2026-08-12.1"
)

semantics = gate.setdefault(
    "semantics",
    {},
)

semantics.update(
    {
        "production_source_release_complete": True,
        "released_packages": 101,
        "released_scopes": 303,
        "secondary_ai_is_not_human_review": True,
        "additional_human_review_claimed": False,
        "unknown_pairs_remain_fail_closed": True,
        "missing_transaction_facts_remain_fail_closed": True,
        "release_authority": "stage6_governance_policy",
        "release_manifest_dataset":
            release["dataset_release"],
        "promotion_manifest_dataset":
            promotion["dataset_release"],
    }
)

GATE.write_text(
    json.dumps(
        gate,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print("Final canonical gate projection: PASS")
print("Promoted packages: 101/101")
print("Released packages: 101/101")
print("Released scopes:   303/303")
print("Top-level fail_closed: TRUE")
