from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class HumanReviewStatus(str, Enum):
    PENDING = "pending"
    COMPLETE = "human_review_complete"


class ProductionApprovalStatus(str, Enum):
    NOT_APPROVED = "not_approved"
    APPROVED = "production_approved"


@dataclass(frozen=True)
class ReviewReleaseOutcome:
    human_review_status: str
    production_approval_status: str
    human_review_complete: bool
    production_approved: bool
    production_releasable: bool
    verified_scope_count: int


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Review event requires {field}.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Review event has invalid {field}.") from exc


def assess_review_release_state(
    package: Mapping[str, Any],
    *,
    human_review_event: Mapping[str, Any] | None = None,
    production_approval_event: Mapping[str, Any] | None = None,
) -> ReviewReleaseOutcome:
    """
    Model the Stage 5 review/release boundary.

    Human review and production approval are distinct actions.

    Completing human review never:
    - marks legal scopes verified;
    - promotes candidate rules;
    - opens the production source-release gate.

    Production approval is also not, by itself, source release. Release
    integration remains a later explicit hash-bound action.
    """

    package_hash = package.get("package_sha256")
    if not isinstance(package_hash, str) or len(package_hash) != 64:
        raise ValueError("Package requires package_sha256.")

    review_complete = False

    if human_review_event is not None:
        if human_review_event.get("package_sha256") != package_hash:
            raise ValueError(
                "Human review event is bound to a stale package hash."
            )

        reviewer_id = human_review_event.get("reviewer_id")
        if not reviewer_id:
            raise ValueError("Human review event requires reviewer_id.")

        _timestamp(
            human_review_event.get("reviewed_at"),
            "reviewed_at",
        )

        if human_review_event.get("outcome") != "accepted":
            raise ValueError(
                "Completed human review requires outcome='accepted'."
            )

        review_complete = True

    production_approved = False

    if production_approval_event is not None:
        if not review_complete:
            raise ValueError(
                "Production approval requires completed human review."
            )

        if production_approval_event.get("package_sha256") != package_hash:
            raise ValueError(
                "Production approval is bound to a stale package hash."
            )

        approver_id = production_approval_event.get("approver_id")
        if not approver_id:
            raise ValueError(
                "Production approval requires approver_id."
            )

        _timestamp(
            production_approval_event.get("approved_at"),
            "approved_at",
        )

        if production_approval_event.get("outcome") != "approved":
            raise ValueError(
                "Production approval requires outcome='approved'."
            )

        production_approved = True

    return ReviewReleaseOutcome(
        human_review_status=(
            HumanReviewStatus.COMPLETE.value
            if review_complete
            else HumanReviewStatus.PENDING.value
        ),
        production_approval_status=(
            ProductionApprovalStatus.APPROVED.value
            if production_approved
            else ProductionApprovalStatus.NOT_APPROVED.value
        ),
        human_review_complete=review_complete,
        production_approved=production_approved,

        # Deliberately fail closed. Production approval is not source release.
        production_releasable=False,

        # Neither review nor approval silently verifies legal rules/scopes.
        verified_scope_count=0,
    )
