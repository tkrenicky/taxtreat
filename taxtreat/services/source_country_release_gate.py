from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from taxtreat.countries.registry import get_country_config


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SourceCountryReleaseDecision:
    source_country: str
    allowed: bool
    code: str
    release_status: str
    blockers: tuple[str, ...]


class SourceCountryNotReleasedError(RuntimeError):
    def __init__(self, decision: SourceCountryReleaseDecision):
        self.decision = decision
        super().__init__(
            f"{decision.source_country} source-country package is not released."
        )


class UnsupportedSourceCountryError(ValueError):
    pass


def _release_manifest_path(code: str) -> Path:
    return (
        ROOT
        / "data"
        / "legal_reviews"
        / f"{code.lower()}_outbound"
        / "source_country_release_manifest.json"
    )


def _fail_release_evidence(
    code: str,
    *,
    decision_code: str,
    blockers: tuple[str, ...],
    release_status: str = "pre_release",
) -> None:
    raise SourceCountryNotReleasedError(
        SourceCountryReleaseDecision(
            source_country=code,
            allowed=False,
            code=decision_code,
            release_status=release_status,
            blockers=blockers,
        )
    )


def _require_committed_release_evidence(code: str) -> None:
    path = _release_manifest_path(code)
    if not path.is_file():
        _fail_release_evidence(
            code,
            decision_code="SOURCE_COUNTRY_RELEASE_EVIDENCE_MISSING",
            blockers=("committed_source_country_release_manifest_missing",),
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _fail_release_evidence(
            code,
            decision_code="SOURCE_COUNTRY_RELEASE_EVIDENCE_INVALID",
            blockers=("committed_source_country_release_manifest_invalid",),
        )

    if not isinstance(payload, dict):
        _fail_release_evidence(
            code,
            decision_code="SOURCE_COUNTRY_RELEASE_EVIDENCE_INVALID",
            blockers=("committed_source_country_release_manifest_invalid",),
        )

    expected = payload.get("expected_scope_count")
    reviewed = payload.get("human_reviewed_scopes")
    cooperating_ready = payload.get("cooperating_state_list_ready")
    calculation_ready = payload.get("final_calculation_policy_ready")
    zero_wht_notification_ready = payload.get("zero_withholding_notification_scope_ready")
    report_gate_ready = payload.get("rendered_report_leakage_gate_ready")
    release_eligible = payload.get("release_eligible")
    status = str(payload.get("release_status") or "pre_release")

    blockers = list(payload.get("blockers") or [])
    if payload.get("source_country") != code:
        blockers.append("release_manifest_source_country_mismatch")
    if not isinstance(expected, int) or expected <= 0:
        blockers.append("release_manifest_expected_scope_count_invalid")
    if reviewed != expected:
        blockers.append("full_human_legal_review_not_completed")
    if cooperating_ready is not True:
        blockers.append("country_specific_legal_source_gates_not_ready")
    if calculation_ready is not True:
        blockers.append("source_country_final_calculation_policy_not_ready")
    if zero_wht_notification_ready is not True:
        blockers.append("source_country_zero_withholding_notification_scope_not_ready")
    if report_gate_ready is not True:
        blockers.append("source_country_rendered_report_leakage_gate_not_ready")
    if release_eligible is not True:
        blockers.append("release_manifest_not_eligible")
    if status != "released":
        blockers.append("release_manifest_status_not_released")

    if blockers:
        _fail_release_evidence(
            code,
            decision_code="SOURCE_COUNTRY_RELEASE_EVIDENCE_INCOMPLETE",
            release_status=status,
            blockers=tuple(dict.fromkeys(blockers)),
        )


def require_source_country_analysis_release(
    source_country: str,
    *,
    released_country_gate: Callable[[str], Any] | None = None,
    release_evidence_gate: Callable[[str], Any] | None = None,
) -> SourceCountryReleaseDecision:
    code = str(source_country or "").upper()
    try:
        config = get_country_config(code)
    except KeyError as exc:
        raise UnsupportedSourceCountryError(code) from exc

    if not config.runtime_released:
        decision = SourceCountryReleaseDecision(
            source_country=code,
            allowed=False,
            code="SOURCE_COUNTRY_NOT_RELEASED",
            release_status="pre_release",
            blockers=(
                "source_country_runtime_release_false",
                "full_human_legal_review_not_completed",
            ),
        )
        raise SourceCountryNotReleasedError(decision)

    if code == "CZ":
        if released_country_gate is not None:
            released_country_gate(code)
    else:
        (release_evidence_gate or _require_committed_release_evidence)(code)

    return SourceCountryReleaseDecision(
        source_country=code,
        allowed=True,
        code="SOURCE_COUNTRY_RELEASED",
        release_status="released",
        blockers=(),
    )
