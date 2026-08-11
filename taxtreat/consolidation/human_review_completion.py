from __future__ import annotations

from datetime import date
from typing import Any, Mapping


def validate_human_review_completion(
    queue: Mapping[str, Any],
    record: Mapping[str, Any],
) -> None:
    packages = queue.get("packages", [])
    recorded = record.get("packages", [])

    if len(packages) != 101:
        raise ValueError("Country QA queue must contain 101 packages.")

    if len(recorded) != 101:
        raise ValueError("Completion record must contain 101 packages.")

    queue_by_pair = {
        package["treaty_pair_id"]: package
        for package in packages
    }

    record_by_pair = {
        package["treaty_pair_id"]: package
        for package in recorded
    }

    if set(queue_by_pair) != set(record_by_pair):
        raise ValueError(
            "Completion record does not match the country-package universe."
        )

    if not record.get("reviewer_id"):
        raise ValueError("Completion record requires reviewer_id.")

    completed_on = record.get("review_completed_on")
    try:
        date.fromisoformat(completed_on)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Completion record has invalid review_completed_on."
        ) from exc

    for pair_id, package in queue_by_pair.items():
        node = record_by_pair[pair_id]

        if node.get("package_sha256") != package.get("package_sha256"):
            raise ValueError(
                f"Completion record has stale package hash: {pair_id}."
            )

        if node.get("scope_count") != 3:
            raise ValueError(
                f"Completion record has invalid scope count: {pair_id}."
            )

        if (
            node.get("primary_human_review_status")
            != "human_review_complete"
        ):
            raise ValueError(
                f"Completion record is not complete: {pair_id}."
            )

    expected_sample = sorted(
        package["treaty_pair_id"]
        for package in packages
        if package["human_qa"]["independent_sample_selected"]
    )

    actual_sample = sorted(
        record["independent_qa"]["selected_pairs"]
    )

    if actual_sample != expected_sample:
        raise ValueError(
            "Independent QA sample does not match the deterministic queue."
        )

    if len(actual_sample) != 7:
        raise ValueError(
            "Expected exactly seven independent QA packages."
        )

    summary = record.get("summary", {})

    expected_zero_fields = (
        "independent_qa_complete_packages",
        "verified_scopes",
        "production_approved_scopes",
        "production_released_scopes",
    )

    for field in expected_zero_fields:
        if summary.get(field) != 0:
            raise ValueError(
                f"Completion record must remain fail closed: {field}."
            )

    if summary.get("country_packages") != 101:
        raise ValueError("Completion summary must contain 101 countries.")

    if summary.get("scopes") != 303:
        raise ValueError("Completion summary must contain 303 scopes.")

    if summary.get("primary_human_review_complete_packages") != 101:
        raise ValueError("All 101 primary reviews must be complete.")

    if summary.get("primary_human_review_complete_scopes") != 303:
        raise ValueError("All 303 scopes must be covered by primary review.")

    if summary.get("independent_qa_pending_packages") != 7:
        raise ValueError("Seven independent QA packages must remain pending.")
