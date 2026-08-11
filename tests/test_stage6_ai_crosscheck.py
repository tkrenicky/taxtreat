from __future__ import annotations

import json
from pathlib import Path

import pytest

from taxtreat.consolidation.secondary_ai_crosscheck import (
    assess_ai_crosscheck,
    assess_human_resolution,
)


ROOT = Path(__file__).parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

QUEUE = BASE / "cz_country_qa_queue.json"
REGISTRY = BASE / "stage6_ai_crosscheck_registry.json"


def _load(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def _packages() -> dict:
    queue = _load(QUEUE)

    return {
        row["treaty_pair_id"]: row
        for row in queue["packages"]
    }


def _clean_event(package: dict) -> dict:
    return {
        "package_sha256":
            package["package_sha256"],
        "treaty_pair_id":
            package["treaty_pair_id"],
        "provider": "external-ai-provider",
        "model": "cross-check-model",
        "run_reference": "manual-run-001",
        "checked_at":
            "2026-08-11T20:00:00Z",
        "outcome": "no_discrepancy",
        "findings": [],
    }


def test_registry_has_exact_seven_country_sample():
    registry = _load(REGISTRY)

    assert [
        row["treaty_pair_id"]
        for row in registry["records"]
    ] == [
        "CZ-AT",
        "CZ-BD",
        "CZ-KP",
        "CZ-KZ",
        "CZ-MY",
        "CZ-SA",
        "CZ-SG",
    ]

    assert registry["summary"][
        "required_packages"
    ] == 7

    assert registry["summary"][
        "ai_crosscheck_complete_packages"
    ] == 7

    assert registry["summary"][
        "ai_crosscheck_pending_packages"
    ] == 0

    assert registry["summary"][
        "clean_packages"
    ] == 2

    assert registry["summary"][
        "packages_with_discrepancies"
    ] == 5

    assert registry["summary"][
        "human_resolution_pending_packages"
    ] == 0

    assert registry["summary"][
        "human_resolution_complete_packages"
    ] == 5

    assert registry["summary"][
        "production_approval_eligible_packages"
    ] == 7


def test_policy_does_not_claim_human_independence():
    policy = _load(REGISTRY)["policy"]

    assert policy["ai_is_human_reviewer"] is False
    assert (
        policy["independent_human_review_claimed"]
        is False
    )


def test_registry_contains_actual_ai_events_without_release():
    registry = _load(REGISTRY)

    by_pair = {
        row["treaty_pair_id"]: row
        for row in registry["records"]
    }

    for pair_id, row in by_pair.items():
        ai = row["ai_crosscheck"]

        assert ai["provider"] == "Anthropic"
        assert ai["model"] == "Sonnet 5"
        assert ai["checked_at"] == (
            "2026-08-11T20:24:04Z"
        )

        assert ai["outcome"] in {
            "no_discrepancy",
            "discrepancy",
        }

        assert ai["status"].startswith(
            "ai_crosscheck_"
        )

    assert by_pair["CZ-KZ"][
        "production_approval_allowed"
    ] is True

    assert by_pair["CZ-SA"][
        "production_approval_allowed"
    ] is True

    for pair_id in {
        "CZ-AT",
        "CZ-BD",
        "CZ-KP",
        "CZ-MY",
        "CZ-SG",
    }:
        assert by_pair[pair_id][
            "production_approval_allowed"
        ] is True

        assert by_pair[pair_id][
            "human_resolution"
        ]["reviewer_id"] == "tkrenicky"

        assert by_pair[pair_id][
            "human_resolution"
        ]["status"] in {
            "tax_treat_corrected",
            "tax_treat_confirmed",
        }

    assert registry["summary"][
        "production_approved_packages"
    ] == 0

    assert registry["summary"][
        "released_packages"
    ] == 0

    assert registry["summary"][
        "released_scopes"
    ] == 0


def test_selected_package_is_pending():
    package = _packages()["CZ-AT"]

    result = assess_ai_crosscheck(package)

    assert result.required is True
    assert result.complete is False
    assert result.status == "pending"
    assert result.production_approval_allowed is False


def test_clean_ai_crosscheck_completes_qa_prerequisite():
    package = _packages()["CZ-AT"]

    result = assess_ai_crosscheck(
        package,
        _clean_event(package),
    )

    assert result.complete is True
    assert result.status == (
        "ai_crosscheck_no_discrepancy"
    )
    assert result.finding_count == 0
    assert result.human_resolution_required is False
    assert result.production_approval_allowed is True


def test_discrepancy_requires_human_resolution():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)

    event["outcome"] = "discrepancy"
    event["findings"] = [
        {
            "topic": "royalties",
            "description": "Potential rate mismatch.",
        }
    ]

    result = assess_ai_crosscheck(
        package,
        event,
    )

    assert result.complete is True
    assert result.finding_count == 1
    assert result.human_resolution_required is True
    assert result.production_approval_allowed is False

    resolution = assess_human_resolution(
        package,
        event,
        None,
        primary_reviewer_id="tkrenicky",
    )

    assert resolution.required is True
    assert resolution.complete is False
    assert (
        resolution.production_approval_allowed
        is False
    )


def test_primary_human_can_resolve_ai_discrepancy():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)

    event["outcome"] = "discrepancy"
    event["findings"] = [
        {
            "topic": "interest",
            "description": "Check exemption condition.",
        }
    ]

    resolution = assess_human_resolution(
        package,
        event,
        {
            "package_sha256":
                package["package_sha256"],
            "treaty_pair_id": "CZ-AT",
            "reviewer_id": "tkrenicky",
            "resolved_at":
                "2026-08-11T21:00:00Z",
            "resolution":
                "tax_treat_confirmed",
            "resolution_note":
                "Checked against primary treaty source.",
        },
        primary_reviewer_id="tkrenicky",
    )

    assert resolution.complete is True
    assert resolution.status == "tax_treat_confirmed"
    assert resolution.production_approval_allowed is True


def test_clean_result_rejects_fake_human_resolution():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)

    with pytest.raises(
        ValueError,
        match="found no discrepancy",
    ):
        assess_human_resolution(
            package,
            event,
            {
                "package_sha256":
                    package["package_sha256"],
                "treaty_pair_id": "CZ-AT",
                "reviewer_id": "tkrenicky",
                "resolved_at":
                    "2026-08-11T21:00:00Z",
                "resolution":
                    "tax_treat_confirmed",
                "resolution_note": "Unnecessary.",
            },
            primary_reviewer_id="tkrenicky",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("provider", "", "requires provider"),
        ("model", "", "requires model"),
        ("checked_at", "bad-date", "invalid checked_at"),
        ("outcome", "accepted", "invalid outcome"),
    ],
)
def test_invalid_ai_metadata_fails_closed(
    field,
    value,
    message,
):
    package = _packages()["CZ-AT"]
    event = _clean_event(package)
    event[field] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_no_discrepancy_cannot_hide_findings():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)

    event["findings"] = [
        {"description": "Hidden discrepancy"}
    ]

    with pytest.raises(
        ValueError,
        match="cannot contain findings",
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_discrepancy_requires_findings():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)

    event["outcome"] = "discrepancy"
    event["findings"] = []

    with pytest.raises(
        ValueError,
        match="requires findings",
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_stale_hash_fails_closed():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)
    event["package_sha256"] = "0" * 64

    with pytest.raises(
        ValueError,
        match="stale package hash",
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_wrong_pair_fails_closed():
    package = _packages()["CZ-AT"]
    event = _clean_event(package)
    event["treaty_pair_id"] = "CZ-BD"

    with pytest.raises(
        ValueError,
        match="different treaty pair",
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_nonselected_package_has_no_ai_crosscheck():
    package = next(
        row
        for row in _packages().values()
        if not row["human_qa"][
            "independent_sample_selected"
        ]
    )

    result = assess_ai_crosscheck(package)

    assert result.required is False
    assert result.status == "not_required"
    assert result.production_approval_allowed is True


def test_historical_review_hash_can_bind_real_ai_event():
    registry = _load(REGISTRY)
    package = _packages()["CZ-AT"]

    record = next(
        row
        for row in registry["records"]
        if row["treaty_pair_id"] == "CZ-AT"
    )

    event = {
        "package_sha256":
            record["reviewed_package_sha256"],
        "treaty_pair_id":
            "CZ-AT",
        "provider":
            record["ai_crosscheck"]["provider"],
        "model":
            record["ai_crosscheck"]["model"],
        "run_reference":
            record["ai_crosscheck"]["run_reference"],
        "checked_at":
            record["ai_crosscheck"]["checked_at"],
        "outcome":
            record["ai_crosscheck"]["outcome"],
        "findings":
            record["ai_crosscheck"]["findings"],
    }

    result = assess_ai_crosscheck(
        package,
        event,
        reviewed_package_sha256=
            record["reviewed_package_sha256"],
    )

    assert result.complete is True
    assert result.human_resolution_required is True
    assert result.production_approval_allowed is False


def test_historical_ai_event_fails_without_hash_lineage():
    registry = _load(REGISTRY)
    package = _packages()["CZ-AT"]

    record = next(
        row
        for row in registry["records"]
        if row["treaty_pair_id"] == "CZ-AT"
    )

    event = {
        "package_sha256":
            record["reviewed_package_sha256"],
        "treaty_pair_id":
            "CZ-AT",
        "provider":
            record["ai_crosscheck"]["provider"],
        "model":
            record["ai_crosscheck"]["model"],
        "run_reference":
            record["ai_crosscheck"]["run_reference"],
        "checked_at":
            record["ai_crosscheck"]["checked_at"],
        "outcome":
            record["ai_crosscheck"]["outcome"],
        "findings":
            record["ai_crosscheck"]["findings"],
    }

    with pytest.raises(
        ValueError,
        match="stale package hash",
    ):
        assess_ai_crosscheck(
            package,
            event,
        )


def test_final_stage6b_resolution_outcomes_are_exact():
    registry = _load(REGISTRY)

    by_pair = {
        row["treaty_pair_id"]: row
        for row in registry["records"]
    }

    expected = {
        "CZ-AT": "tax_treat_corrected",
        "CZ-BD": "tax_treat_corrected",
        "CZ-KP": "tax_treat_corrected",
        "CZ-MY": "tax_treat_corrected",
        "CZ-SG": "tax_treat_confirmed",
    }

    for pair_id, outcome in expected.items():
        assert (
            by_pair[pair_id][
                "human_resolution"
            ]["status"]
            == outcome
        )

    assert (
        by_pair["CZ-KZ"][
            "human_resolution"
        ]["status"]
        == "not_required"
    )

    assert (
        by_pair["CZ-SA"][
            "human_resolution"
        ]["status"]
        == "not_required"
    )


def test_stage6b_completion_does_not_create_production_release():
    registry = _load(REGISTRY)

    summary = registry["summary"]

    assert summary[
        "production_approval_eligible_packages"
    ] == 7

    assert summary[
        "production_approved_packages"
    ] == 0

    assert summary["promoted_packages"] == 0
    assert summary["released_packages"] == 0
    assert summary["released_scopes"] == 0
