from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


AI_OUTCOMES = {
    "no_discrepancy",
    "discrepancy",
    "unable_to_conclude",
}


@dataclass(frozen=True)
class AICrossCheckOutcome:
    required: bool
    complete: bool
    status: str
    provider: str | None
    model: str | None
    finding_count: int
    human_resolution_required: bool
    production_approval_allowed: bool


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"AI cross-check event requires {field}."
        )

    try:
        datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            f"AI cross-check event has invalid {field}."
        ) from exc


def assess_ai_crosscheck(
    package: Mapping[str, Any],
    event: Mapping[str, Any] | None = None,
) -> AICrossCheckOutcome:

    package_hash = package.get("package_sha256")

    if (
        not isinstance(package_hash, str)
        or len(package_hash) != 64
    ):
        raise ValueError(
            "AI cross-check requires package_sha256."
        )

    human_qa = package.get("human_qa", {})

    # Historical Stage 5 field name is retained only
    # as the deterministic sample-selection source.
    required = bool(
        human_qa.get("independent_sample_selected")
    )

    if not required:
        if event is not None:
            raise ValueError(
                "AI cross-check event supplied for a "
                "package outside the selected sample."
            )

        return AICrossCheckOutcome(
            required=False,
            complete=False,
            status="not_required",
            provider=None,
            model=None,
            finding_count=0,
            human_resolution_required=False,
            production_approval_allowed=True,
        )

    if event is None:
        return AICrossCheckOutcome(
            required=True,
            complete=False,
            status="pending",
            provider=None,
            model=None,
            finding_count=0,
            human_resolution_required=False,
            production_approval_allowed=False,
        )

    if event.get("package_sha256") != package_hash:
        raise ValueError(
            "AI cross-check event is bound to a "
            "stale package hash."
        )

    pair_id = package.get("treaty_pair_id")

    if event.get("treaty_pair_id") != pair_id:
        raise ValueError(
            "AI cross-check event is bound to a "
            "different treaty pair."
        )

    provider = event.get("provider")
    model = event.get("model")

    if not isinstance(provider, str) or not provider.strip():
        raise ValueError(
            "AI cross-check event requires provider."
        )

    if not isinstance(model, str) or not model.strip():
        raise ValueError(
            "AI cross-check event requires model."
        )

    _timestamp(
        event.get("checked_at"),
        "checked_at",
    )

    outcome = event.get("outcome")

    if outcome not in AI_OUTCOMES:
        raise ValueError(
            "AI cross-check event has an invalid outcome."
        )

    findings = event.get("findings")

    if not isinstance(findings, list):
        raise ValueError(
            "AI cross-check event requires findings list."
        )

    if outcome == "no_discrepancy" and findings:
        raise ValueError(
            "No-discrepancy event cannot contain findings."
        )

    if (
        outcome in {"discrepancy", "unable_to_conclude"}
        and not findings
    ):
        raise ValueError(
            "Discrepancy or uncertainty requires findings."
        )

    human_resolution_required = (
        outcome != "no_discrepancy"
    )

    return AICrossCheckOutcome(
        required=True,
        complete=True,
        status=f"ai_crosscheck_{outcome}",
        provider=provider,
        model=model,
        finding_count=len(findings),
        human_resolution_required=human_resolution_required,

        # A clean AI cross-check completes this QA prerequisite.
        # Any discrepancy/uncertainty remains blocked until
        # separately resolved by the human primary reviewer.
        production_approval_allowed=(
            not human_resolution_required
        ),
    )


@dataclass(frozen=True)
class HumanResolutionOutcome:
    required: bool
    complete: bool
    status: str
    production_approval_allowed: bool


def assess_human_resolution(
    package: Mapping[str, Any],
    ai_event: Mapping[str, Any],
    resolution_event: Mapping[str, Any] | None,
    *,
    primary_reviewer_id: str,
) -> HumanResolutionOutcome:

    ai_result = assess_ai_crosscheck(
        package,
        ai_event,
    )

    if not ai_result.human_resolution_required:
        if resolution_event is not None:
            raise ValueError(
                "Human resolution event supplied when "
                "AI cross-check found no discrepancy."
            )

        return HumanResolutionOutcome(
            required=False,
            complete=True,
            status="not_required",
            production_approval_allowed=True,
        )

    if resolution_event is None:
        return HumanResolutionOutcome(
            required=True,
            complete=False,
            status="pending_human_resolution",
            production_approval_allowed=False,
        )

    if (
        resolution_event.get("package_sha256")
        != package.get("package_sha256")
    ):
        raise ValueError(
            "Human resolution event is bound to a "
            "stale package hash."
        )

    if (
        resolution_event.get("treaty_pair_id")
        != package.get("treaty_pair_id")
    ):
        raise ValueError(
            "Human resolution event is bound to a "
            "different treaty pair."
        )

    reviewer_id = resolution_event.get("reviewer_id")

    if reviewer_id != primary_reviewer_id:
        raise ValueError(
            "AI discrepancy resolution must be recorded "
            "by the primary human reviewer."
        )

    _timestamp(
        resolution_event.get("resolved_at"),
        "resolved_at",
    )

    resolution = resolution_event.get("resolution")

    if resolution not in {
        "tax_treat_confirmed",
        "tax_treat_corrected",
    }:
        raise ValueError(
            "Human resolution event has invalid resolution."
        )

    note = resolution_event.get("resolution_note")

    if not isinstance(note, str) or not note.strip():
        raise ValueError(
            "Human resolution event requires resolution_note."
        )

    return HumanResolutionOutcome(
        required=True,
        complete=True,
        status=resolution,
        production_approval_allowed=True,
    )
