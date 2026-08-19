from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from taxtreat.tools.build_sk_domestic_review_readiness import (
    build_readiness as build_domestic_readiness,
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

INGESTION_SUMMARY_PATH = SK_DIR / "machine_ingestion_run_summary.json"
MLI_EXTRACTION_SUMMARY_PATH = SK_DIR / "mli_notice_machine_extraction_summary.json"
TREATY_EXTRACTION_SUMMARY_PATH = SK_DIR / "treaty_article_machine_extraction_summary.json"
SEMANTIC_SUMMARY_PATH = SK_DIR / "treaty_semantic_candidates_summary.json"
OUTPUT_PATH = SK_DIR / "pre_review_readiness.json"


def _load_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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

    treaty_relationships_extracted = (
        ingestion.get("treaty_relationships_machine_extracted", 0)
        if ingestion else 0
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
    if treaty_relationships_extracted != 75:
        blockers.append("not_all_75_treaty_relationships_machine_extracted")
    if mli_relationships_extracted != 46:
        blockers.append("not_all_46_mli_relationships_machine_extracted")
    if semantic_candidates != 225:
        blockers.append("not_all_225_treaty_scopes_have_semantic_candidates")
    if not domestic["cooperating_state_list"]["ingestion_complete"]:
        blockers.append("official_2026_cooperating_state_list_body_not_ingested")
    if reconciliation_summary["unresolved_notice_mismatches"]:
        blockers.append("mli_notice_instrument_chain_mismatch_unresolved")

    all_machine_evidence_ready = not blockers

    return {
        "schema_version": 1,
        "dataset_release": "sk-pre-review-readiness-2026-08-19.1",
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
            "treaty_relationships_extracted": treaty_relationships_extracted,
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
        },
        "mli_instrument_chain": {
            "relationships": reconciliation_summary["relationship_count"],
            "resolved_relationships": reconciliation_summary["resolved_relationships"],
            "unresolved_notice_mismatches": reconciliation_summary[
                "unresolved_notice_mismatches"
            ],
        },
        "human_review": {
            "started": False,
            "reviewed_scopes": 0,
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
