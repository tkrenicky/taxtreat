from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from taxtreat.tools.evaluate_sk_domestic_transaction_candidates import (
    evaluate_domestic_transaction_candidates,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = (
    ROOT
    / "data"
    / "legal_reviews"
    / "sk_outbound"
    / "prerelease_runtime_manifest.json"
)


@dataclass(frozen=True)
class SkPrereleaseCandidateResult:
    status: str
    source_country: str
    recipient_country: str
    income_type: str
    scope_key: tuple[str, str, str]
    candidate_only: bool
    requires_review: bool
    final_rate_percent: float | None
    candidate_domestic_treatment: str | None
    treaty_semantic_candidate: dict[str, Any] | None
    mli_applicable: bool | None
    blockers: tuple[str, ...]
    missing_transaction_facts: tuple[str, ...]
    runtime_dependency_source_countries: tuple[str, ...]
    czech_runtime_fallback_used: bool
    runtime_released: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scope_row(
    manifest: dict[str, Any],
    recipient_country: str,
    income_type: str,
) -> dict[str, Any] | None:
    key = ("SK", recipient_country, income_type)
    return next(
        (
            row
            for row in manifest.get("scopes", [])
            if tuple(row.get("scope_key", ())) == key
        ),
        None,
    )


def _dependency_sources(*values: Any) -> tuple[str, ...]:
    sources = {
        str(value).upper()
        for value in values
        if value is not None and str(value).strip()
    }
    return tuple(sorted(sources))


def _dependency_blockers(sources: tuple[str, ...]) -> list[str]:
    foreign = [source for source in sources if source != "SK"]
    if not foreign:
        return []
    blockers = ["foreign_runtime_dependency_detected"]
    if "CZ" in foreign:
        blockers.append("czech_runtime_dependency_detected")
    return blockers


def _dividend_domestic_candidate(
    facts: dict[str, Any],
    *,
    cooperating_state_list_ready: bool,
) -> tuple[str | None, list[str], list[str]]:
    required_transaction_facts = (
        "recipient_entity_type",
        "distribution_category_is_section_3_1_f",
        "distribution_is_tax_deductible_for_payer",
    )
    missing = [
        name for name in required_transaction_facts if facts.get(name) is None
    ]
    blockers: list[str] = []

    if not cooperating_state_list_ready:
        blockers.append("official_2026_cooperating_state_status_unresolved")

    if missing:
        return None, missing, blockers

    if facts["recipient_entity_type"] != "corporate":
        return "section_12_7_c_not_applicable_non_corporate_recipient", [], blockers

    if facts["distribution_category_is_section_3_1_f"] is True:
        return "section_12_7_c_exception_section_3_1_f_candidate", [], blockers

    if facts["distribution_is_tax_deductible_for_payer"] is True:
        return "section_12_7_c_outside_subject_rule_not_available_to_deductible_extent", [], blockers

    if not cooperating_state_list_ready:
        return "section_12_7_c_outside_subject_candidate_pending_cooperating_state_status", [], blockers

    return "section_12_7_c_candidate_requires_source_backed_cooperating_state_fact", [], [
        *blockers,
        "source_backed_cooperating_state_fact_not_connected",
    ]


def evaluate_sk_prerelease_candidate(
    *,
    recipient_country: str,
    income_type: str,
    facts: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> SkPrereleaseCandidateResult:
    country = str(recipient_country or "").upper()
    income = str(income_type or "").lower()
    facts = dict(facts or {})
    manifest = manifest or _load_manifest()

    if manifest.get("source_country") != "SK":
        raise ValueError("SK prerelease evaluator requires an SK manifest.")
    if manifest.get("policy", {}).get("runtime_release") is not False:
        raise ValueError("Prerelease evaluator must never consume a released manifest.")

    row = _scope_row(manifest, country, income)
    scope_key = ("SK", country, income)
    base_dependencies = _dependency_sources(
        manifest.get("source_country"),
        row.get("source_country") if row else None,
    )
    if row is None:
        return SkPrereleaseCandidateResult(
            status="OUT_OF_SCOPE",
            source_country="SK",
            recipient_country=country,
            income_type=income,
            scope_key=scope_key,
            candidate_only=True,
            requires_review=False,
            final_rate_percent=None,
            candidate_domestic_treatment=None,
            treaty_semantic_candidate=None,
            mli_applicable=None,
            blockers=tuple(_dependency_blockers(base_dependencies)),
            missing_transaction_facts=(),
            runtime_dependency_source_countries=base_dependencies,
            czech_runtime_fallback_used="CZ" in base_dependencies,
            runtime_released=False,
        )

    blockers = [
        "full_human_legal_review_not_completed",
        "sk_runtime_release_not_completed",
    ]
    missing: list[str] = []
    dependencies = base_dependencies

    if not row.get("cooperating_state_list_ready"):
        blockers.append("official_2026_cooperating_state_list_body_not_ingested")

    evidence_status = str(row.get("treaty_machine_evidence_status") or "")
    if "primary_summary_fallback" in evidence_status:
        blockers.append("treaty_primary_summary_fallback_requires_human_review")

    if row.get("mli_applicable"):
        if row.get("mli_machine_evidence_status") != "completed":
            blockers.append("pair_specific_mli_machine_evidence_incomplete")
        if not row.get("mli_wht_effective_dates"):
            blockers.append("pair_specific_mli_wht_effective_date_missing")

    if income == "dividend":
        domestic_treatment, missing, domestic_blockers = _dividend_domestic_candidate(
            facts,
            cooperating_state_list_ready=bool(
                row.get("cooperating_state_list_ready")
            ),
        )
        blockers.extend(domestic_blockers)
    elif income in {"interest", "royalty"}:
        domestic = evaluate_domestic_transaction_candidates(income, facts)
        dependencies = _dependency_sources(
            *dependencies,
            domestic.get("source_country"),
        )
        pe = domestic["registered_pe_exclusion"]
        relief = domestic["eu_relief"]
        missing = sorted(
            set(pe.get("missing_facts", []))
            | set(relief.get("missing_facts", []))
        )
        if pe.get("applies") is True:
            domestic_treatment = "registered_sk_pe_withholding_exclusion_candidate"
        else:
            domestic_treatment = relief.get("candidate_treatment")
    else:
        dependencies = base_dependencies
        return SkPrereleaseCandidateResult(
            status="OUT_OF_SCOPE",
            source_country="SK",
            recipient_country=country,
            income_type=income,
            scope_key=scope_key,
            candidate_only=True,
            requires_review=False,
            final_rate_percent=None,
            candidate_domestic_treatment=None,
            treaty_semantic_candidate=None,
            mli_applicable=bool(row.get("mli_applicable")),
            blockers=tuple(_dependency_blockers(dependencies)),
            missing_transaction_facts=(),
            runtime_dependency_source_countries=dependencies,
            czech_runtime_fallback_used="CZ" in dependencies,
            runtime_released=False,
        )

    blockers.extend(_dependency_blockers(dependencies))

    treaty_candidate = row.get("treaty_semantic_candidate")

    return SkPrereleaseCandidateResult(
        status="REVIEW_REQUIRED",
        source_country="SK",
        recipient_country=country,
        income_type=income,
        scope_key=scope_key,
        candidate_only=True,
        requires_review=True,
        final_rate_percent=None,
        candidate_domestic_treatment=domestic_treatment,
        treaty_semantic_candidate=treaty_candidate,
        mli_applicable=bool(row.get("mli_applicable")),
        blockers=tuple(dict.fromkeys(blockers)),
        missing_transaction_facts=tuple(missing),
        runtime_dependency_source_countries=dependencies,
        czech_runtime_fallback_used="CZ" in dependencies,
        runtime_released=False,
    )
