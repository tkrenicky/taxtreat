from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

HUMAN_REVIEW = BASE / "stage5_human_review_completion.json"
LEGACY_GATE = BASE / "production_source_release_gate.json"

OUTPUT = BASE / "production_source_release_gate_v2.json"
SUMMARY = BASE / "production_source_release_gate_v2_summary.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


review = read_json(HUMAN_REVIEW)
legacy = read_json(LEGACY_GATE)

review_packages = review["packages"]

if len(review_packages) != 101:
    raise RuntimeError(
        f"Expected 101 reviewed packages, found {len(review_packages)}."
    )

if review["summary"]["scopes"] != 303:
    raise RuntimeError("Expected exactly 303 WHT scopes.")

legacy_by_pair = {
    row["treaty_pair_id"]: row
    for row in legacy["treaty_partners"]
}

rows = []

for package in sorted(
    review_packages,
    key=lambda row: row["treaty_pair_id"],
):
    pair_id = package["treaty_pair_id"]
    partner = package["partner_country"]

    old = legacy_by_pair.get(pair_id)

    legacy_evidence = (
        old.get("release_evidence", {})
        if old
        else {}
    )

    rows.append(
        {
            "treaty_pair_id": pair_id,
            "partner_country": partner,
            "package_sha256": package["package_sha256"],

            "human_review_status": (
                package["primary_human_review_status"]
            ),

            # Stage 6A deliberately creates no approval.
            "independent_qa_status": "pending"
            if pair_id in review["independent_qa"]["selected_pairs"]
            else "not_required",

            "production_approval_status": "not_approved",
            "rule_promotion_status": "not_promoted",

            # No package is released by this migration.
            "release_status": "blocked",
            "active_rule_allowed": False,
            "production_ready": False,
            "fail_closed": True,

            "release_blockers": [
                *(
                    ["independent_qa_pending"]
                    if pair_id
                    in review["independent_qa"]["selected_pairs"]
                    else []
                ),
                "production_approval_missing",
                "rule_promotion_missing",
                "source_release_not_opened",
            ],

            "release_evidence": {
                "stage5_package_sha256":
                    package["package_sha256"],

                # Retained only as historical/source provenance.
                "legacy_release_evidence":
                    legacy_evidence,

                "production_approval_event":
                    None,

                "rule_promotion_event":
                    None,

                "source_release_event":
                    None,
            },
        }
    )

pair_ids = [row["treaty_pair_id"] for row in rows]

if len(pair_ids) != 101:
    raise RuntimeError("Canonical gate must contain 101 country packages.")

if len(pair_ids) != len(set(pair_ids)):
    raise RuntimeError("Duplicate treaty pair in canonical release gate.")

selected = sorted(
    review["independent_qa"]["selected_pairs"]
)

if len(selected) != 7:
    raise RuntimeError(
        "Expected exactly seven independent QA packages."
    )

released = [
    row
    for row in rows
    if row["release_status"] == "released"
]

if released:
    raise RuntimeError(
        "Stage 6A migration must not release any country."
    )

payload = {
    "schema_version": 2,
    "dataset_release":
        "production-source-release-gate-v2-2026-08-11.1",

    "universe": {
        "country_package_count": 101,
        "scope_count": 303,
    },

    "migration_from": {
        "dataset_release":
            legacy.get("dataset_release"),
        "legacy_treaty_partner_count":
            legacy.get("treaty_partner_count"),
        "legacy_gate_is_authority_for_release":
            False,
        "legacy_evidence_retained_as_provenance":
            True,
    },

    "gate_semantics": {
        "global_fail_closed": True,
        "human_review_is_not_production_approval": True,
        "production_approval_is_not_rule_promotion": True,
        "rule_promotion_is_not_source_release": True,
        "missing_release_event_blocks_runtime": True,
        "automatic_needs_review_to_verified_forbidden": True,
    },

    "counts": {
        "treaty_partner_count": 101,
        "scope_count": 303,
        "human_review_complete_packages": 101,
        "independent_qa_pending_packages": 7,
        "production_approved_packages": 0,
        "rule_promoted_packages": 0,
        "released_packages": 0,
        "released_scopes": 0,
    },

    "fail_closed": True,
    "treaty_partner_count": 101,
    "treaty_partners": rows,
}

summary = {
    "schema_version": 1,
    "dataset_release":
        "production-source-release-gate-v2-summary-2026-08-11.1",

    "country_package_count": 101,
    "scope_count": 303,

    "human_review_complete_packages": 101,
    "independent_qa_required_packages": 7,
    "independent_qa_complete_packages": 0,

    "production_approved_packages": 0,
    "rule_promoted_packages": 0,
    "released_packages": 0,
    "released_scopes": 0,

    "fail_closed": True,

    "independent_qa_pairs": selected,
}

write_json(OUTPUT, payload)
write_json(SUMMARY, summary)

print("Stage 6 canonical release gate created.")
print("Countries:", len(rows))
print("Scopes: 303")
print("Independent QA pending:", len(selected))
print("Released countries:", len(released))
