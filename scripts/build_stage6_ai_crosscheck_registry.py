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
COMPLETION = BASE / "stage5_human_review_completion.json"

OUTPUT = BASE / "stage6_ai_crosscheck_registry.json"
SUMMARY = BASE / "stage6_ai_crosscheck_registry_summary.json"


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
completion = read_json(COMPLETION)

packages = {
    row["treaty_pair_id"]: row
    for row in queue["packages"]
}

# Historical sample selection remains unchanged.
selected = sorted(
    completion["independent_qa"]["selected_pairs"]
)

expected = [
    "CZ-AT",
    "CZ-BD",
    "CZ-KP",
    "CZ-KZ",
    "CZ-MY",
    "CZ-SA",
    "CZ-SG",
]

if selected != expected:
    raise RuntimeError(
        "AI cross-check sample changed unexpectedly."
    )

records = []

for pair_id in selected:
    package = packages[pair_id]

    records.append(
        {
            "treaty_pair_id": pair_id,
            "partner_country":
                package["partner_country"],

            "package_sha256":
                package["package_sha256"],

            "scope_count": 3,

            "primary_human_reviewer_id":
                completion["reviewer_id"],

            "ai_crosscheck": {
                "provider": None,
                "model": None,
                "run_reference": None,
                "checked_at": None,
                "outcome": None,
                "findings": [],
                "status": "pending",
            },

            "human_resolution": {
                "reviewer_id": None,
                "resolved_at": None,
                "resolution": None,
                "resolution_note": None,
                "status": "not_required_yet",
            },

            "production_approval_allowed":
                False,
        }
    )

payload = {
    "schema_version": 1,

    "dataset_release":
        "stage6-ai-crosscheck-registry-2026-08-11.1",

    "purpose":
        "Secondary AI cross-check of the deterministic "
        "Stage 6 QA sample before production approval.",

    "policy": {
        "selected_package_count": 7,

        "primary_human_reviewer_id":
            completion["reviewer_id"],

        "crosscheck_type":
            "secondary_ai_cross_check",

        "ai_is_human_reviewer":
            False,

        "independent_human_review_claimed":
            False,

        "different_model_or_session_preferred":
            True,

        "exact_package_hash_required":
            True,

        "provider_and_model_must_be_recorded":
            True,

        "ai_findings_do_not_self_modify_legal_content":
            True,

        "human_resolution_required_for_discrepancies":
            True,

        "human_resolution_required_for_uncertainty":
            True,

        "clean_ai_result_requires_no_extra_human_rereview":
            True,

        "ai_crosscheck_is_not_production_approval":
            True,

        "ai_crosscheck_is_not_rule_promotion":
            True,

        "ai_crosscheck_is_not_source_release":
            True,

        "fabricated_ai_event_forbidden":
            True,
    },

    "summary": {
        "required_packages": 7,
        "ai_crosscheck_complete_packages": 0,
        "ai_crosscheck_pending_packages": 7,

        "clean_packages": 0,
        "packages_with_discrepancies": 0,
        "uncertain_packages": 0,

        "human_resolution_pending_packages": 0,
        "human_resolution_complete_packages": 0,

        "production_approved_packages": 0,
        "promoted_packages": 0,
        "released_packages": 0,
        "released_scopes": 0,
    },

    "records": records,
}

summary = {
    "schema_version": 1,

    "dataset_release":
        "stage6-ai-crosscheck-registry-summary-2026-08-11.1",

    "required_packages": 7,
    "complete_packages": 0,
    "pending_packages": 7,

    "clean_packages": 0,
    "discrepancy_packages": 0,
    "uncertain_packages": 0,

    "production_approved_packages": 0,
    "released_packages": 0,
    "released_scopes": 0,

    "selected_pairs": selected,

    "crosscheck_type":
        "secondary_ai_cross_check",

    "independent_human_review_claimed":
        False,
}

write_json(OUTPUT, payload)
write_json(SUMMARY, summary)

print("AI cross-check registry created.")
print("Required:", len(records))
print("Complete: 0")
print("Pending:", len(records))
print("Human reviewer:", completion["reviewer_id"])
