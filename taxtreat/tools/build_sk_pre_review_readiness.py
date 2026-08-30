from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.tools.build_sk_domestic_review_readiness import (
    build_readiness as build_domestic_readiness,
)
from taxtreat.tools.build_sk_prerelease_runtime_manifest import (
    build_manifest as build_runtime_manifest,
    build_summary as build_runtime_manifest_summary,
)
from taxtreat.tools.build_sk_review_preparation import (
    build_machine_preparation,
    build_summary as build_machine_summary,
)
from taxtreat.tools.reconcile_sk_mli_instrument_chain import (
    build_reconciliation,
    build_summary as build_reconciliation_summary,
)


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"
HUMAN_REVIEW_COVERAGE_PATH = SK_DIR / "human_review_coverage.json"

INGESTION_SUMMARY_PATH = SK_DIR / "machine_ingestion_run_summary.json"
MLI_EXTRACTION_SUMMARY_PATH = SK_DIR / "mli_notice_machine_extraction_summary.json"
TREATY_EXTRACTION_SUMMARY_PATH = SK_DIR / "treaty_article_machine_extraction_summary.json"
SEMANTIC_SUMMARY_PATH = SK_DIR / "treaty_semantic_candidates_summary.json"
COMPLIANCE_PROFILE_PATH = SK_DIR / "compliance_profile_2026.json"
DIVIDEND_MODEL_PATH = SK_DIR / "dividend_domestic_condition_model.json"
OUTPUT_PATH = SK_DIR / "pre_review_readiness.json"


def _load_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _compliance_profile_status() -> dict[str, Any]:
    profile = _load_if_exists(COMPLIANCE_PROFILE_PATH)
    if profile is None:
        return {
            "present": False,
            "country_specific": False,
            "monthly_section_43_11_modelled": False,
            "czech_reuse_prohibited": False,
            "runtime_release": False,
        }

    policy = profile.get("policy", {})
    ordinary = profile.get("ordinary_corporate_outbound_wht", {})
    notification = ordinary.get("notification", {})
    remittance = ordinary.get("remittance", {})

    return {
        "present": True,
        "country_specific": (
            profile.get("source_country") == "SK"
            and policy.get("country_specific_compliance_required") is True
        ),
        "monthly_section_43_11_modelled": (
            notification.get("form_code") == "OZN4311v26"
            and notification.get("periodicity") == "monthly"
            and notification.get("legal_reference") == "§ 43 ods. 11"
            and remittance.get("legal_reference") == "§ 43 ods. 11"
            and remittance.get("same_deadline_as_notification") is True
        ),
        "czech_reuse_prohibited": (
            policy.get("czech_deadlines_or_forms_must_not_be_reused") is True
            and policy.get("czech_statutory_references_must_not_be_reused") is True
        ),
        "ordinary_annual_wht_return_configured": profile.get(
            "annual_reporting", {}
        ).get("ordinary_dividend_interest_royalty_annual_wht_return_configured"),
        "form_code": notification.get("form_code"),
        "runtime_release": policy.get("runtime_release") is True,
    }


def _dividend_model_status() -> dict[str, Any]:
    model = _load_if_exists(DIVIDEND_MODEL_PATH)
    if model is None:
        return {
            "present": False,
            "slovak_specific": False,
            "outside_subject_rule_modelled": False,
            "2026_source_version": False,
            "non_cooperating_state_gate_preserved": False,
            "runtime_release": False,
        }

    policy = model.get("policy", {})
    primary_rule = model.get("primary_rule", {})
    exceptions = {
        row.get("exception_id"): row
        for row in model.get("exceptions", [])
    }
    source = (model.get("primary_sources") or [{}])[0]

    return {
        "present": True,
        "slovak_specific": (
            model.get("source_country") == "SK"
            and policy.get(
                "slovak_domestic_law_is_independent_from_czech_parent_subsidiary_rules"
            ) is True
        ),
        "outside_subject_rule_modelled": (
            primary_rule.get("legal_reference") == "§ 12 ods. 7 písm. c)"
            and primary_rule.get("treatment")
            == "outside_subject_of_corporate_income_tax_candidate"
        ),
        "2026_source_version": (
            model.get("law_effective_from") == "2026-01-01"
            and model.get("law_effective_to") == "2026-12-30"
            and str(source.get("url", "")).endswith("/20260101.print.html")
        ),
        "non_cooperating_state_gate_preserved": (
            exceptions.get("non_cooperating_state_legal_entity", {}).get(
                "machine_status"
            )
            == "blocked_until_official_2026_cooperating_state_list_body_is_ingested"
        ),
        "distribution_deductibility_required": (
            "distribution_is_tax_deductible_for_payer"
            in model.get("required_transaction_facts", [])
        ),
        "runtime_release": policy.get("runtime_release") is True,
    }


def build_readiness() -> dict[str, Any]:
    machine = build_machine_preparation()
    machine_summary = build_machine_summary(machine)
    domestic = build_domestic_readiness()
    reconciliation = build_reconciliation()
    reconciliation_summary = build_reconciliation_summary(reconciliation)

    ingestion = _load_if_exists(INGESTION_SUMMARY_PATH)
    mli_extraction = _load_if_exists(MLI_EXTRACTION_SUMMARY_PATH)
    treaty_extraction = _load_if_exists(TREATY_EXTRACTION_SUMMARY_PATH)
    semantic = _load_if_exists(SEMANTIC_SUMMARY_PATH)
    compliance = _compliance_profile_status()
    dividend_model = _dividend_model_status()

    runtime_manifest = None
    runtime_manifest_summary = None
    try:
        runtime_manifest = build_runtime_manifest()
        runtime_manifest_summary = build_runtime_manifest_summary(runtime_manifest)
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        runtime_manifest = None
        runtime_manifest_summary = None

    treaty_relationships_ready = 0
    treaty_primary_summary_fallbacks = 0
    if ingestion:
        treaty_relationships_ready = ingestion.get(
            "treaty_relationships_machine_evidence_ready",
            ingestion.get("treaty_relationships_machine_extracted", 0),
        )
        treaty_primary_summary_fallbacks = ingestion.get(
            "treaty_primary_summary_fallback_relationships", 0
        )

    mli_relationships_extracted = (
        ingestion.get("mli_relationships_machine_extracted", 0)
        if ingestion else 0
    )
    semantic_candidates = (
        ingestion.get("semantic_candidate_scopes", 0)
        if ingestion else 0
    )

    blockers: list[str] = []
    if ingestion is None:
        blockers.append("full_machine_ingestion_not_run")
    if treaty_relationships_ready != 75:
        blockers.append("not_all_75_treaty_relationships_have_machine_evidence")
    if mli_relationships_extracted != 46:
        blockers.append("not_all_46_mli_relationships_machine_extracted")
    if semantic_candidates != 225:
        blockers.append("not_all_225_treaty_scopes_have_semantic_candidates")
    if not domestic["cooperating_state_list"]["ingestion_complete"]:
        blockers.append("official_2026_cooperating_state_list_body_not_ingested")
    if reconciliation_summary["unresolved_notice_mismatches"]:
        blockers.append("mli_notice_instrument_chain_mismatch_unresolved")
    if not compliance["present"]:
        blockers.append("sk_2026_compliance_profile_missing")
    elif not (
        compliance["country_specific"]
        and compliance["monthly_section_43_11_modelled"]
        and compliance["czech_reuse_prohibited"]
    ):
        blockers.append("sk_2026_compliance_profile_incomplete")
    if not dividend_model["present"]:
        blockers.append("sk_dividend_domestic_model_missing")
    elif not (
        dividend_model["slovak_specific"]
        and dividend_model["outside_subject_rule_modelled"]
        and dividend_model["2026_source_version"]
        and dividend_model["non_cooperating_state_gate_preserved"]
        and dividend_model["distribution_deductibility_required"]
    ):
        blockers.append("sk_dividend_domestic_model_incomplete")
    if runtime_manifest_summary is None:
        blockers.append("sk_prerelease_runtime_manifest_not_ready")
    elif (
        runtime_manifest_summary.get("scope_count") != 225
        or runtime_manifest_summary.get("mli_scopes") != 138
        or runtime_manifest_summary.get("production_released_scopes") != 0
    ):
        blockers.append("sk_prerelease_runtime_manifest_incomplete")

    all_machine_evidence_ready = not blockers

    return {
        "schema_version": 5,
        "dataset_release": "sk-pre-review-readiness-2026-08-19.5",
        "source_country": "SK",
        "target": {
            "country_relationships": 75,
            "treaty_scopes": 225,
            "mli_relationships": 46,
            "human_review_start_policy": "only_after_complete_machine_evidence_for_entire_sk_scope",
            "production_parity_target": "same_functional_and_legal_quality_as_current_czech_web_branch",
        },
        "machine_preparation": {
            "scopes": machine_summary["machine_prepared_scopes"],
            "review_ready_scopes_from_initial_preparation": machine_summary[
                "review_ready_scopes"
            ],
        },
        "machine_ingestion": {
            "run_completed": ingestion is not None,
            "treaty_relationships_machine_evidence_ready": treaty_relationships_ready,
            "treaty_primary_summary_fallback_relationships": treaty_primary_summary_fallbacks,
            "mli_relationships_extracted": mli_relationships_extracted,
            "semantic_candidate_scopes": semantic_candidates,
            "raw_summary": ingestion,
            "mli_extraction_summary": mli_extraction,
            "treaty_extraction_summary": treaty_extraction,
            "semantic_summary": semantic,
        },
        "domestic": {
            "cooperating_state_list_ingestion_complete": domestic[
                "cooperating_state_list"
            ]["ingestion_complete"],
            "domestic_rate_branch_machine_ready": domestic["review_ready"],
            "eu_interest_royalty_and_pe_condition_model_present": True,
            "dividend_model": dividend_model,
        },
        "compliance": compliance,
        "prerelease_runtime_manifest": runtime_manifest_summary,
        "mli_instrument_chain": {
            "relationships": reconciliation_summary["relationship_count"],
            "resolved_relationships": reconciliation_summary["resolved_relationships"],
            "unresolved_notice_mismatches": reconciliation_summary[
                "unresolved_notice_mismatches"
            ],
        },
        "human_review": {
            "started": True,
            "reviewed_scopes": _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["individually_reviewed_scopes"],
            "pattern_reconciled_scopes": _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["pattern_reconciled_scopes"],
            "legal_review_covered_scopes": _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["legal_review_covered_scopes"],
            "completed": (
                _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["legal_review_covered_scopes"]
                == _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["expected_scope_count"]
                and _load_if_exists(HUMAN_REVIEW_COVERAGE_PATH)["coverage"]["uncovered_scopes"] == 0
            ),
            "may_start": all_machine_evidence_ready,
        },
        "runtime": {
            "released": False,
            "production_released_scopes": 0,
        },
        "all_machine_evidence_ready": all_machine_evidence_ready,
        "blockers": blockers,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_readiness()
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
