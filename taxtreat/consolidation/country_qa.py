from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class CountryRisk(str, Enum):
    STANDARD = "STANDARD"
    ELEVATED = "ELEVATED"
    EXCEPTION = "EXCEPTION"


EXCEPTION_FEATURES = {
    "conflicting_primary_evidence",
    "unresolved_legal_effect",
    "treaty_status_uncertainty",
    "effective_date_conflict",
}

ELEVATED_FEATURES = {
    "unusual_treaty_numbering",
    "material_protocol_overlay",
    "wht_relevant_mli_modification",
    "multiple_historical_instruments",
    "unusual_language_or_prevailing_text",
    "preserved_historical_source_hash_difference",
}

SAMPLE_PERCENT = {
    CountryRisk.STANDARD: 10,
    CountryRisk.ELEVATED: 20,
    CountryRisk.EXCEPTION: 100,
}
METHODOLOGY_VERSION = "cz-country-qa-v1"


def classify_country_risk(features: set[str]) -> CountryRisk:
    unknown = features - EXCEPTION_FEATURES - ELEVATED_FEATURES
    if unknown:
        raise ValueError("Unsupported country-risk features: " + ", ".join(sorted(unknown)))
    if features & EXCEPTION_FEATURES:
        return CountryRisk.EXCEPTION
    if features & ELEVATED_FEATURES:
        return CountryRisk.ELEVATED
    return CountryRisk.STANDARD


def selected_for_independent_sample(
    treaty_pair_id: str,
    risk: CountryRisk | str,
) -> bool:
    category = CountryRisk(risk)
    token = f"{METHODOLOGY_VERSION}:{treaty_pair_id.upper()}".encode("ascii")
    bucket = int(hashlib.sha256(token).hexdigest()[:8], 16) % 100
    return bucket < SAMPLE_PERCENT[category]


@dataclass(frozen=True)
class CountryQAOutcome:
    country_qa_complete: bool
    independent_review_required: bool
    independent_review_complete: bool
    package_status: str
    scopes_marked_verified: int
    production_release_allowed: bool


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Country QA event requires {field}.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Country QA event has invalid {field}.") from exc


def apply_country_qa_event(
    package: Mapping[str, Any],
    event: Mapping[str, Any] | None,
) -> CountryQAOutcome:
    """Validate a future human event without promoting any scope or rule.

    The country check is a release prerequisite, not legal verification.  Rule
    promotion remains an explicit, separately hash-bound human action.
    """

    risk = CountryRisk(package["risk_category"])
    pair_id = str(package["treaty_pair_id"])
    independent_required = (
        risk is CountryRisk.EXCEPTION
        or selected_for_independent_sample(pair_id, risk)
    )
    if event is None:
        return CountryQAOutcome(
            country_qa_complete=False,
            independent_review_required=independent_required,
            independent_review_complete=False,
            package_status="awaiting_country_qa",
            scopes_marked_verified=0,
            production_release_allowed=False,
        )

    if event.get("package_sha256") != package.get("package_sha256"):
        raise ValueError("Country QA event is bound to a stale package hash.")
    reviewer_id = event.get("reviewer_id")
    if not reviewer_id:
        raise ValueError("Country QA event requires reviewer_id.")
    _timestamp(event.get("reviewed_at"), "reviewed_at")
    if event.get("outcome") not in {"accepted", "returned_for_correction"}:
        raise ValueError("Country QA event has an invalid outcome.")
    if event["outcome"] == "returned_for_correction":
        return CountryQAOutcome(
            country_qa_complete=False,
            independent_review_required=independent_required,
            independent_review_complete=False,
            package_status="returned_for_correction",
            scopes_marked_verified=0,
            production_release_allowed=False,
        )

    independent_complete = False
    if independent_required:
        approver_id = event.get("independent_reviewer_id")
        if not approver_id:
            raise ValueError("Selected country package requires independent_reviewer_id.")
        if approver_id == reviewer_id:
            raise ValueError("Country reviewer and independent reviewer must differ.")
        _timestamp(event.get("independently_reviewed_at"), "independently_reviewed_at")
        if event.get("independent_outcome") != "accepted":
            raise ValueError("Required independent review must be accepted.")
        independent_complete = True

    return CountryQAOutcome(
        country_qa_complete=True,
        independent_review_required=independent_required,
        independent_review_complete=independent_complete,
        package_status="country_qa_complete",
        scopes_marked_verified=0,
        production_release_allowed=False,
    )
