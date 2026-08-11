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

QUEUE = BASE / "cz_country_qa_queue.json"
HUMAN_REVIEW = BASE / "stage5_human_review_completion.json"
AI_REGISTRY = BASE / "stage6_ai_crosscheck_registry.json"
PRODUCTION_APPROVAL = BASE / "stage6_production_approval.json"
LEGACY_GATE = BASE / "production_source_release_gate.json"

OUTPUT = BASE / "production_source_release_gate_v2.json"
SUMMARY = BASE / "production_source_release_gate_v2_summary.json"


def read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


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


queue = read_json(QUEUE)
review = read_json(HUMAN_REVIEW)
ai_registry = read_json(AI_REGISTRY)
production_approval = read_json(PRODUCTION_APPROVAL)
legacy = read_json(LEGACY_GATE)

packages = queue["packages"]

if len(packages) != 101:
    raise RuntimeError(
        f"Expected 101 current packages, found {len(packages)}."
    )

if review["summary"]["scopes"] != 303:
    raise RuntimeError(
        "Expected exactly 303 WHT scopes."
    )

review_by_pair = {
    row["treaty_pair_id"]: row
    for row in review["packages"]
}

ai_by_pair = {
    row["treaty_pair_id"]: row
    for row in ai_registry["records"]
}

selected = sorted(
    ai_registry["summary"]
    and [
        row["treaty_pair_id"]
        for row in ai_registry["records"]
    ]
)

expected_selected = [
    "CZ-AT",
    "CZ-BD",
    "CZ-KP",
    "CZ-KZ",
    "CZ-MY",
    "CZ-SA",
    "CZ-SG",
]

if selected != expected_selected:
    raise RuntimeError(
        "Stage 6 AI sample changed unexpectedly."
    )

if (
    ai_registry["summary"][
        "ai_crosscheck_complete_packages"
    ]
    != 7
):
    raise RuntimeError(
        "Stage 6 AI cross-check is not complete."
    )

if (
    ai_registry["summary"][
        "human_resolution_pending_packages"
    ]
    != 0
):
    raise RuntimeError(
        "Stage 6 human resolutions remain pending."
    )

if (
    ai_registry["summary"][
        "human_resolution_complete_packages"
    ]
    != 5
):
    raise RuntimeError(
        "Expected exactly five completed resolutions."
    )

if (
    ai_registry["summary"][
        "production_approved_packages"
    ]
    != 0
):
    raise RuntimeError(
        "Stage 6C readiness builder must not consume "
        "pre-existing production approvals."
    )


legacy_by_pair = {
    row["treaty_pair_id"]: row
    for row in legacy["treaty_partners"]
}

approval_by_pair = {
    row["treaty_pair_id"]: row
    for row in production_approval["records"]
}

if len(approval_by_pair) != 101:
    raise RuntimeError(
        "Production approval must contain exactly 101 packages."
    )

if production_approval.get(
    "additional_human_review_claimed"
) is not False:
    raise RuntimeError(
        "Stage 6C must not claim an additional human review."
    )

if production_approval["counts"][
    "production_approved_packages"
] != 101:
    raise RuntimeError(
        "Production approval package count must equal 101."
    )

if production_approval["counts"][
    "production_approved_scopes"
] != 303:
    raise RuntimeError(
        "Production approval scope count must equal 303."
    )


rows = []

for package in sorted(
    packages,
    key=lambda row: row["treaty_pair_id"],
):
    pair_id = package["treaty_pair_id"]
    partner = package["partner_country"]
    current_hash = package["package_sha256"]

    review_node = review_by_pair[pair_id]

    old = legacy_by_pair.get(pair_id)

    legacy_evidence = (
        old.get("release_evidence", {})
        if old
        else {}
    )

    if pair_id in ai_by_pair:
        ai_node = ai_by_pair[pair_id]

        if (
            ai_node["current_package_sha256"]
            != current_hash
        ):
            raise RuntimeError(
                f"Stage 6 AI registry has stale current hash: "
                f"{pair_id}."
            )

        if (
            ai_node["production_approval_allowed"]
            is not True
        ):
            raise RuntimeError(
                f"QA sample package is not approval eligible: "
                f"{pair_id}."
            )

        qa_status = "secondary_ai_crosscheck_complete"

        qa_evidence = {
            "crosscheck_status":
                ai_node["ai_crosscheck"]["status"],
            "ai_outcome":
                ai_node["ai_crosscheck"]["outcome"],
            "reviewed_package_sha256":
                ai_node["reviewed_package_sha256"],
            "current_package_sha256":
                ai_node["current_package_sha256"],
            "human_resolution_status":
                ai_node["human_resolution"]["status"],
        }

    else:
        qa_status = "not_selected"

        qa_evidence = {
            "crosscheck_status": "not_selected",
            "ai_outcome": None,
            "reviewed_package_sha256": None,
            "current_package_sha256":
                current_hash,
            "human_resolution_status":
                "not_required",
        }

    approval_node = approval_by_pair.get(pair_id)

    if approval_node is None:
        raise RuntimeError(
            f"Missing production approval record: {pair_id}."
        )

    if approval_node["package_sha256"] != current_hash:
        raise RuntimeError(
            f"Production approval hash mismatch: {pair_id}."
        )

    if (
        approval_node["production_approval_status"]
        != "production_approved"
    ):
        raise RuntimeError(
            f"Package is not production approved: {pair_id}."
        )

    blockers = [
        "rule_promotion_missing",
        "source_release_not_opened",
    ]

    rows.append(
        {
            "treaty_pair_id": pair_id,
            "partner_country": partner,

            # Current post-Stage-6B package hash.
            "package_sha256": current_hash,

            "human_review_status":
                review_node[
                    "primary_human_review_status"
                ],

            # No second human review is required in the current
            # Stage 6 governance model. Secondary AI cross-checking
            # is represented separately below and must never be
            # described as independent human QA.
            "independent_qa_status":
                "not_required",

            "secondary_ai_qa_status":
                qa_status,

            "production_approval_status":
                "production_approved",

            "production_approval_eligible":
                True,

            "rule_promotion_status":
                "not_promoted",

            "release_status":
                "blocked",

            "active_rule_allowed":
                False,

            "production_ready":
                False,

            "fail_closed":
                True,

            "release_blockers":
                blockers,

            "release_evidence": {
                "stage5_review_record_package_sha256":
                    review_node["package_sha256"],

                "current_package_sha256":
                    current_hash,

                "stage6_qa_evidence":
                    qa_evidence,

                "legacy_release_evidence":
                    legacy_evidence,

                "production_approval_event": {
                    "dataset_release":
                        production_approval["dataset_release"],
                    "event_type":
                        production_approval["event_type"],
                    "approval_authority":
                        production_approval[
                            "approval_authority"
                        ],
                    "additional_human_review_claimed":
                        production_approval[
                            "additional_human_review_claimed"
                        ],
                    "created_at":
                        production_approval["created_at"],
                    "package_sha256":
                        current_hash,
                },

                "rule_promotion_event":
                    None,

                "source_release_event":
                    None,
            },
        }
    )


pair_ids = [
    row["treaty_pair_id"]
    for row in rows
]

if len(pair_ids) != 101:
    raise RuntimeError(
        "Canonical gate must contain 101 packages."
    )

if len(pair_ids) != len(set(pair_ids)):
    raise RuntimeError(
        "Duplicate treaty pair in canonical gate."
    )

if any(
    row["production_approval_status"]
    != "production_approved"
    for row in rows
):
    raise RuntimeError(
        "All 101 packages must be production approved."
    )

if any(
    row["rule_promotion_status"]
    != "not_promoted"
    for row in rows
):
    raise RuntimeError(
        "Readiness migration must not promote rules."
    )

if any(
    row["release_status"] != "blocked"
    for row in rows
):
    raise RuntimeError(
        "Readiness migration must remain fail closed."
    )


payload = {
    "schema_version": 2,

    "dataset_release":
        "production-source-release-gate-v2-2026-08-11.2",

    "universe": {
        "country_package_count": 101,
        "scope_count": 303,
    },

    "gate_semantics": {
        "global_fail_closed": True,

        "primary_human_review_complete":
            True,

        "secondary_ai_crosscheck_sample_complete":
            True,

        "secondary_ai_is_not_human_review":
            True,

        "production_approval_is_explicit_event":
            True,

        "production_approval_is_deterministic_governance_result":
            True,

        "production_approval_is_additional_human_review":
            False,

        "production_approval_is_not_rule_promotion":
            True,

        "rule_promotion_is_not_source_release":
            True,

        "missing_release_event_blocks_runtime":
            True,

        "automatic_needs_review_to_verified_forbidden":
            True,
    },

    "counts": {
        "treaty_partner_count": 101,
        "scope_count": 303,

        "human_review_complete_packages": 101,

        "secondary_ai_crosscheck_required_packages": 7,
        "secondary_ai_crosscheck_complete_packages": 7,
        "secondary_ai_crosscheck_pending_packages": 0,

        "human_resolution_complete_packages": 5,
        "human_resolution_pending_packages": 0,

        "production_approval_eligible_packages": 101,
        "production_approved_packages": 101,

        "rule_promoted_packages": 0,

        "released_packages": 0,
        "released_scopes": 0,
    },

    "fail_closed": True,
    "treaty_partner_count": 101,
    "treaty_partners": rows,
}


summary = {
    "schema_version": 2,

    "dataset_release":
        "production-source-release-gate-v2-summary-2026-08-11.2",

    "country_package_count": 101,
    "scope_count": 303,

    "human_review_complete_packages": 101,

    "secondary_ai_crosscheck_required_packages": 7,
    "secondary_ai_crosscheck_complete_packages": 7,
    "secondary_ai_crosscheck_pending_packages": 0,

    "human_resolution_complete_packages": 5,
    "human_resolution_pending_packages": 0,

    "production_approval_eligible_packages": 101,
    "production_approved_packages": 101,

    "rule_promoted_packages": 0,

    "released_packages": 0,
    "released_scopes": 0,

    "fail_closed": True,

    "secondary_ai_pairs":
        expected_selected,
}


write_json(OUTPUT, payload)
write_json(SUMMARY, summary)

print("Stage 6C production approval readiness gate created.")
print("Countries: 101")
print("Scopes: 303")
print("Primary human review complete: 101")
print("Secondary AI QA complete: 7/7")
print("Human discrepancy resolutions complete: 5/5")
print("Production approval eligible: 101")
print("Production approved: 101")
print("Promoted: 0")
print("Released: 0")
