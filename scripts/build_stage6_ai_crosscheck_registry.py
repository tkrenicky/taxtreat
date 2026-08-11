from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from taxtreat.consolidation.secondary_ai_crosscheck import (
    assess_ai_crosscheck,
    assess_human_resolution,
)


BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

QUEUE = BASE / "cz_country_qa_queue.json"
COMPLETION = BASE / "stage5_human_review_completion.json"
AI_EVENTS = BASE / "stage6_ai_crosscheck_events.json"
RESOLUTIONS = BASE / "stage6_human_resolution_events.json"

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
ai_payload = read_json(AI_EVENTS)
resolution_payload = read_json(RESOLUTIONS)

packages = {
    row["treaty_pair_id"]: row
    for row in queue["packages"]
}

completion_by_pair = {
    row["treaty_pair_id"]: row
    for row in completion["packages"]
}

ai_events = {
    row["treaty_pair_id"]: row
    for row in ai_payload["events"]
}

resolution_events = {
    row["treaty_pair_id"]: row
    for row in resolution_payload["events"]
}

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

if sorted(ai_events) != expected:
    raise RuntimeError(
        "AI event universe does not match exact sample."
    )

expected_resolution_pairs = {
    pair_id
    for pair_id, event in ai_events.items()
    if event["outcome"] != "no_discrepancy"
}

if set(resolution_events) != expected_resolution_pairs:
    raise RuntimeError(
        "Human resolution universe does not match "
        "the discrepancy universe."
    )


records = []

clean_count = 0
discrepancy_count = 0
uncertain_count = 0
resolution_complete_count = 0
resolution_pending_count = 0
approval_allowed_count = 0


for pair_id in selected:
    package = packages[pair_id]
    completion_node = completion_by_pair[pair_id]
    ai_event = ai_events[pair_id]

    current_hash = package["package_sha256"]

    reviewed_hash = completion_node.get(
        "reviewed_package_sha256",
        current_hash,
    )

    ai_result = assess_ai_crosscheck(
        package,
        ai_event,
        reviewed_package_sha256=reviewed_hash,
    )

    if not ai_result.complete:
        raise RuntimeError(
            f"AI event is incomplete: {pair_id}."
        )

    if ai_event["outcome"] == "no_discrepancy":
        clean_count += 1

        human_resolution = {
            "reviewer_id": None,
            "resolved_at": None,
            "resolution": None,
            "resolution_note": None,
            "status": "not_required",
        }

        approval_allowed = True

    else:
        if ai_event["outcome"] == "discrepancy":
            discrepancy_count += 1
        else:
            uncertain_count += 1

        resolution_event = resolution_events.get(
            pair_id
        )

        resolution_result = assess_human_resolution(
            package,
            ai_event,
            resolution_event,
            primary_reviewer_id=
                completion["reviewer_id"],
            reviewed_package_sha256=
                reviewed_hash,
        )

        if resolution_result.complete:
            resolution_complete_count += 1
        else:
            resolution_pending_count += 1

        human_resolution = {
            "reviewer_id":
                resolution_event.get("reviewer_id")
                if resolution_event
                else None,
            "resolved_at":
                resolution_event.get("resolved_at")
                if resolution_event
                else None,
            "resolution":
                resolution_event.get("resolution")
                if resolution_event
                else None,
            "resolution_note":
                resolution_event.get("resolution_note")
                if resolution_event
                else None,
            "status":
                resolution_result.status,
        }

        approval_allowed = (
            resolution_result.production_approval_allowed
        )

    if approval_allowed:
        approval_allowed_count += 1

    records.append({
        "treaty_pair_id": pair_id,
        "partner_country":
            package["partner_country"],

        "package_sha256":
            current_hash,
        "current_package_sha256":
            current_hash,

        # Exact package reviewed by secondary AI.
        "reviewed_package_sha256":
            reviewed_hash,

        "scope_count": 3,

        "primary_human_reviewer_id":
            completion["reviewer_id"],

        "ai_crosscheck": {
            "provider":
                ai_event["provider"],
            "model":
                ai_event["model"],
            "run_reference":
                ai_event.get("run_reference"),
            "checked_at":
                ai_event["checked_at"],
            "timestamp_basis":
                ai_event.get("timestamp_basis"),
            "outcome":
                ai_event["outcome"],
            "findings":
                ai_event["findings"],
            "status":
                ai_result.status,
        },

        "human_resolution":
            human_resolution,

        # Eligibility to move to Stage 6C only.
        # This is NOT production approval.
        "production_approval_allowed":
            approval_allowed,
    })


payload = {
    "schema_version": 1,

    "dataset_release":
        "stage6-ai-crosscheck-registry-2026-08-11.3",

    "purpose":
        "Completed Stage 6 secondary AI cross-check and "
        "required primary-human discrepancy resolutions "
        "before production approval.",

    "policy": {
        "selected_package_count": 7,

        "primary_human_reviewer_id":
            completion["reviewer_id"],

        "crosscheck_type":
            "secondary_ai_cross_check",

        "supplementary_work_adjudication_recorded":
            True,

        "ai_is_human_reviewer":
            False,

        "independent_human_review_claimed":
            False,

        "exact_reviewed_package_hash_required":
            True,

        "post_review_correction_hash_lineage_supported":
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

        "human_resolution_is_not_production_approval":
            True,

        "production_approval_is_not_rule_promotion":
            True,

        "rule_promotion_is_not_source_release":
            True,

        "fabricated_ai_event_forbidden":
            True,

        "fabricated_human_resolution_forbidden":
            True,
    },

    "summary": {
        "required_packages": 7,
        "ai_crosscheck_complete_packages": 7,
        "ai_crosscheck_pending_packages": 0,

        "clean_packages":
            clean_count,
        "packages_with_discrepancies":
            discrepancy_count,
        "uncertain_packages":
            uncertain_count,

        "human_resolution_pending_packages":
            resolution_pending_count,
        "human_resolution_complete_packages":
            resolution_complete_count,

        "production_approval_eligible_packages":
            approval_allowed_count,

        # Stage 6C has not happened.
        "production_approved_packages": 0,

        # Stage 6D/6E have not happened.
        "promoted_packages": 0,
        "released_packages": 0,
        "released_scopes": 0,
    },

    "records": records,
}


summary = {
    "schema_version": 1,

    "dataset_release":
        "stage6-ai-crosscheck-registry-summary-2026-08-11.3",

    "required_packages": 7,
    "complete_packages": 7,
    "pending_packages": 0,

    "clean_packages":
        clean_count,
    "discrepancy_packages":
        discrepancy_count,
    "uncertain_packages":
        uncertain_count,

    "human_resolution_complete_packages":
        resolution_complete_count,
    "human_resolution_pending_packages":
        resolution_pending_count,

    "production_approval_eligible_packages":
        approval_allowed_count,

    "production_approved_packages": 0,
    "released_packages": 0,
    "released_scopes": 0,

    "selected_pairs": selected,

    "crosscheck_type":
        "secondary_ai_cross_check",

    "secondary_ai": {
        "provider": "Anthropic",
        "model": "Sonnet 5",
        "effort": "Medium",
    },

    "supplementary_ai": {
        "provider": "OpenAI",
        "model": "GPT-5.6 Sol",
        "effort": "Medium",
    },

    "independent_human_review_claimed":
        False,
}


write_json(OUTPUT, payload)
write_json(SUMMARY, summary)

print("Stage 6 AI registry rebuilt.")
print("AI cross-check complete: 7/7")
print(
    "Human resolutions complete:",
    resolution_complete_count,
    "/5",
)
print(
    "Production approval eligible:",
    approval_allowed_count,
    "/7",
)
print("Production approved: 0")
print("Promoted: 0")
print("Released: 0")
