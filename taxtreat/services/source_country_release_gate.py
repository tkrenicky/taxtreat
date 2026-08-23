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
    config = get_country_config(code)

    if config.release_manifest_path is not None:
        return Path(config.release_manifest_path)

    return (
        ROOT
        / "data"
        / "legal_reviews"
        / f"{code.lower()}_outbound"
        / "source_country_release_manifest.json"
    )


def _review_coverage_blockers(
    manifest: dict[str, Any],
    manifest_path: Path,
) -> tuple[str, ...]:
    """Validate canonical legal-review coverage evidence fail-closed."""

    blockers: list[str] = []
    policy = manifest.get("policy")
    if not isinstance(policy, dict):
        return ("release_manifest_review_policy_invalid",)

    individual_only = policy.get("all_expected_scopes_must_be_human_reviewed")
    coverage_enabled = policy.get("all_expected_scopes_must_be_legally_covered")

    if coverage_enabled is not True:
        if individual_only is False:
            return ("release_manifest_legal_review_coverage_policy_missing",)
        return ()

    evidence_name = manifest.get("human_review_evidence")
    if not isinstance(evidence_name, str) or not evidence_name.strip():
        return ("legal_review_coverage_evidence_missing",)

    evidence_path = manifest_path.parent / evidence_name
    if not evidence_path.is_file():
        return ("legal_review_coverage_evidence_missing",)

    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ("legal_review_coverage_evidence_invalid",)

    if not isinstance(evidence, dict):
        return ("legal_review_coverage_evidence_invalid",)

    if evidence.get("source_country") != manifest.get("source_country"):
        blockers.append("legal_review_coverage_source_country_mismatch")

    coverage_status = str(evidence.get("status") or "")
    if not coverage_status.startswith(
        "human_review_completed_with_pattern_reconciliation"
    ):
        blockers.append("legal_review_coverage_status_incomplete")

    coverage = evidence.get("coverage")
    if not isinstance(coverage, dict):
        return tuple(blockers + ["legal_review_coverage_evidence_invalid"])

    expected = manifest.get("expected_scope_count")
    evidence_expected = coverage.get("expected_scope_count")
    individual = coverage.get("individually_reviewed_scopes")
    pattern = coverage.get("pattern_reconciled_scopes")
    covered = coverage.get("legal_review_covered_scopes")
    uncovered = coverage.get("uncovered_scopes")

    numeric_values = (expected, evidence_expected, individual, pattern, covered, uncovered)
    if not all(isinstance(value, int) and value >= 0 for value in numeric_values):
        blockers.append("legal_review_coverage_counts_invalid")
        return tuple(blockers)

    if evidence_expected != expected:
        blockers.append("legal_review_coverage_expected_scope_mismatch")

    if individual != manifest.get("human_reviewed_scopes"):
        blockers.append("legal_review_individual_count_manifest_mismatch")

    if pattern != manifest.get("pattern_reconciled_scopes"):
        blockers.append("legal_review_pattern_count_manifest_mismatch")

    if covered != manifest.get("legal_review_covered_scopes"):
        blockers.append("legal_review_covered_count_manifest_mismatch")

    if individual + pattern != covered:
        blockers.append("legal_review_coverage_count_mismatch")

    if covered != expected or uncovered != 0:
        blockers.append("full_legal_review_coverage_not_completed")

    reconciliation = evidence.get("pattern_reconciliation")
    if not isinstance(reconciliation, dict):
        blockers.append("legal_review_pattern_reconciliation_missing")
    else:
        if reconciliation.get("scope_count") != pattern:
            blockers.append("legal_review_pattern_scope_count_mismatch")
        if reconciliation.get("result") != "COVERED_BY_VALIDATED_STANDARD_PATTERN":
            blockers.append("legal_review_pattern_reconciliation_incomplete")
        if reconciliation.get("individual_human_review_claimed") is not False:
            blockers.append("legal_review_pattern_false_individual_review_claim")

    individual_review = evidence.get("individual_review")
    if not isinstance(individual_review, dict):
        blockers.append("legal_review_individual_evidence_missing")
    else:
        if individual_review.get("substantive_machine_discrepancies") != 0:
            blockers.append("legal_review_substantive_discrepancy_unresolved")
        if individual_review.get("exceptions") != 0:
            blockers.append("legal_review_exception_unresolved")

    if evidence.get("production_released_scopes") != 0:
        blockers.append("legal_review_evidence_preclaims_production_release")

    return tuple(dict.fromkeys(blockers))


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
    compliance_calendar_ready = payload.get("compliance_calendar_adjustment_ready")
    report_gate_ready = payload.get("rendered_report_leakage_gate_ready")
    release_eligible = payload.get("release_eligible")
    status = str(payload.get("release_status") or "pre_release")

    blockers = list(payload.get("blockers") or [])
    if payload.get("source_country") != code:
        blockers.append("release_manifest_source_country_mismatch")
    if not isinstance(expected, int) or expected <= 0:
        blockers.append("release_manifest_expected_scope_count_invalid")
    policy = payload.get("policy")
    coverage_policy = (
        isinstance(policy, dict)
        and policy.get("all_expected_scopes_must_be_legally_covered") is True
    )

    if coverage_policy:
        blockers.extend(_review_coverage_blockers(payload, path))
    elif reviewed != expected:
        blockers.append("full_human_legal_review_not_completed")
    if cooperating_ready is not True:
        blockers.append("country_specific_legal_source_gates_not_ready")
    if calculation_ready is not True:
        blockers.append("source_country_final_calculation_policy_not_ready")
    if zero_wht_notification_ready is not True:
        blockers.append("source_country_zero_withholding_notification_scope_not_ready")
    if compliance_calendar_ready is not True:
        blockers.append("source_country_compliance_calendar_adjustment_not_ready")
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

    if config.release_gate_strategy == "canonical_stage6":
        if released_country_gate is not None:
            released_country_gate(code)

    elif config.release_gate_strategy == "source_country_manifest":
        (release_evidence_gate or _require_committed_release_evidence)(code)

    else:
        raise ValueError(
            f"Unsupported release gate strategy for {code}: "
            f"{config.release_gate_strategy}"
        )

    return SourceCountryReleaseDecision(
        source_country=code,
        allowed=True,
        code="SOURCE_COUNTRY_RELEASED",
        release_status="released",
        blockers=(),
    )
