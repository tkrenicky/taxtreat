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
    ] == 0

    assert registry["summary"][
        "ai_crosscheck_pending_packages"
    ] == 7


def test_policy_does_not_claim_human_independence():
    policy = _load(REGISTRY)["policy"]

    assert policy["ai_is_human_reviewer"] is False
    assert (
        policy["independent_human_review_claimed"]
        is False
    )


def test_registry_contains_no_fake_ai_event():
    registry = _load(REGISTRY)

    for row in registry["records"]:
        ai = row["ai_crosscheck"]

        assert ai["provider"] is None
        assert ai["model"] is None
        assert ai["checked_at"] is None
        assert ai["outcome"] is None
        assert ai["findings"] == []
        assert ai["status"] == "pending"

        assert (
            row["production_approval_allowed"]
            is False
        )


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
