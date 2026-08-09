from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_stage5_batch01_legal_chain_dossier import (  # noqa: E402
    ARTICLE_HEADINGS_BY_INCOME,
    income_article_evidence,
    instrument_classification,
    scope_present,
)
from build_stage5_remaining80_batch01_intake import (  # noqa: E402
    resolve_source_manifest_row,
)


EXECUTION = ROOT / "data/legal_consolidation/stage5_execution_manifest.json"
INVENTORY = ROOT / "data/legal_consolidation/mf_inventory.json"
SOURCE_MANIFEST = ROOT / "data/manifests/source_manifest.json"
FROZEN_CHAINS = ROOT / "data/legal_consolidation/remaining_294_instrument_chains.json"
DOMESTIC_EU = ROOT / "data/legal_consolidation/cz_domestic_eu_candidates.json"
BATCH01_DOSSIER = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining80_batch_01_legal_chain_dossier.json"
)
PILOT_EVIDENCE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "at_ch_existing_source_evidence.json"
)
MIGRATION_BOUNDARY = ROOT / "data/legal_consolidation/final23_migration_boundary.json"
OUTPUT_DIR = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_remaining70_candidate_evidence"
)
INDEX_OUTPUT = OUTPUT_DIR / "index.json"
COVERAGE_OUTPUT = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage5_candidate_coverage_registry.json"
)

INCOMES = ("dividend", "interest", "royalty")


def load(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(f"Required file missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def signature_clause_candidates(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    seen = set()

    for article_index, article in enumerate(parsed.get("articles") or []):
        text = article.get("text")
        if not isinstance(text, str):
            continue

        for match in re.finditer(r"^[ \t]*D[áa]no\b", text, flags=re.MULTILINE):
            tail = text[match.start():]
            ends = [
                item.start()
                for item in re.finditer(
                    r"\n(?:Za\s|Na\s+d[uůí]kaz)", tail, flags=re.IGNORECASE
                )
                if item.start() > 20
            ]
            excerpt = (tail[: min(ends)] if ends else tail).strip()
            excerpt_hash = sha256_bytes(excerpt.encode("utf-8"))
            if excerpt_hash in seen:
                continue
            seen.add(excerpt_hash)
            candidates.append(
                {
                    "json_path": f"$.articles[{article_index}].text",
                    "article_number": article.get("number"),
                    "article_title": article.get("title"),
                    "exact_excerpt": excerpt,
                    "excerpt_sha256": excerpt_hash,
                }
            )

    return candidates


def source_binding(source: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    parsed_value = source.get("parsed_path")
    artifact_value = source.get("artifact_uri")
    blockers = []

    if not isinstance(parsed_value, str) or not (ROOT / parsed_value).is_file():
        raise RuntimeError("resolved source lacks repository parsed artifact")
    if not isinstance(artifact_value, str):
        raise RuntimeError("resolved source lacks archived artifact URI")

    parsed_path = ROOT / parsed_value
    artifact_path = ROOT / artifact_value
    expected_artifact_hash = source.get("sha256")
    artifact_present = artifact_path.is_file()
    observed_artifact_hash = sha256_file(artifact_path) if artifact_present else None

    if artifact_present and observed_artifact_hash == expected_artifact_hash:
        relation = "matches_manifest"
        artifact_hash_valid = True
    elif artifact_present:
        relation = "mismatch"
        artifact_hash_valid = False
        blockers.append("archived_artifact_hash_mismatch")
    else:
        relation = "not_comparable"
        artifact_hash_valid = False
        blockers.append("archived_artifact_bytes_unavailable_fresh_official_extraction_required")

    return (
        {
            "source_id": source.get("source_id"),
            "source_title": source.get("source_title"),
            "authority_class": source.get("authority_class"),
            "identity_status": source.get("identity_status"),
            "identity_warnings": source.get("identity_warnings") or [],
            "official_urls": source.get("official_urls") or [],
            "parsed_path": parsed_value,
            "parsed_sha256": sha256_file(parsed_path),
            "artifact_uri": artifact_value,
            "archived_manifest_sha256": expected_artifact_hash,
            "artifact_bytes_present": artifact_present,
            "observed_artifact_sha256": observed_artifact_hash,
            "artifact_hash_valid": artifact_hash_valid,
            "artifact_hash_relation": relation,
        },
        blockers,
    )


def build() -> dict[str, Any]:
    execution = load(EXECUTION)
    inventory = load(INVENTORY)
    source_manifest = load(SOURCE_MANIFEST)
    frozen = load(FROZEN_CHAINS)
    domestic = load(DOMESTIC_EU)
    batch01 = load(BATCH01_DOSSIER)

    for relative, expected_hash in execution["frozen_remaining_294_hashes"].items():
        if sha256_file(ROOT / relative) != expected_hash:
            raise RuntimeError(f"Frozen remaining_294 hash changed: {relative}")

    batches = execution["remaining80_work_batches"]
    batch01_countries = set(batches[0]["countries"])
    remaining70 = [country for batch in batches[1:] for country in batch["countries"]]

    if len(remaining70) != 70 or len(set(remaining70)) != 70:
        raise RuntimeError("Expected exactly 70 unique post-Batch-01 countries")
    if batch01_countries & set(remaining70):
        raise RuntimeError("Batch 01 overlaps remaining70 boundary")

    partners = {entry["iso2"]: entry for entry in inventory["partners"]}
    sources = [entry for entry in source_manifest["sources"] if isinstance(entry, dict)]
    frozen_by_scope = {
        f"CZ-{entry['recipient_country']}-{entry['income_type']}": (index, entry)
        for index, entry in enumerate(frozen["scopes"])
    }

    entries = []
    resolved_article_count = 0
    signature_status_counts: Counter[str] = Counter()
    source_resolution_counts: Counter[str] = Counter()
    article_conflicts = []

    for country in remaining70:
        partner = partners[country]
        country_blockers = [
            "human_primary_legal_review_required",
            "independent_approval_required",
            "language_authority_interpretation_required",
            "withholding_effective_date_review_required",
            "mli_and_instrument_effect_review_required",
        ]

        try:
            source, resolution_method = resolve_source_manifest_row(partner, sources)
            binding, binding_blockers = source_binding(source)
            parsed = load(ROOT / binding["parsed_path"])
            article_map = {
                income: income_article_evidence(parsed, income)
                for income in ARTICLE_HEADINGS_BY_INCOME
            }
            signature_candidates = signature_clause_candidates(parsed)
            source_status = "resolved"
            source_error = None
            country_blockers.extend(binding_blockers)
            if binding["authority_class"] != "official":
                country_blockers.append("canonical_source_not_official")
            if binding["identity_status"] != "validated":
                country_blockers.append("canonical_source_identity_not_validated")
        except RuntimeError as exc:
            binding = None
            resolution_method = None
            source_error = str(exc)
            source_status = "unresolved"
            article_map = {
                income: {
                    "income_type": income,
                    "article_number": None,
                    "resolved": False,
                    "resolution_status": "unresolved",
                    "evidence_count": 0,
                    "evidence": [],
                }
                for income in ARTICLE_HEADINGS_BY_INCOME
            }
            signature_candidates = []
            country_blockers.append("canonical_treaty_source_unresolved")

        source_resolution_counts[source_status] += 1
        if len(signature_candidates) == 1:
            signature_status = "single_candidate_needs_review"
        elif not signature_candidates:
            signature_status = "unresolved"
            country_blockers.append("signature_clause_candidate_not_resolved")
        else:
            signature_status = "ambiguous_multiple_candidates"
            country_blockers.append("signature_clause_candidate_ambiguous")
        signature_status_counts[signature_status] += 1

        related = instrument_classification(partner)
        scopes = []

        for income in INCOMES:
            scope_id = f"CZ-{country}-{income}"
            article = article_map[income]
            frozen_item = frozen_by_scope.get(scope_id)
            scope_blockers = []

            if frozen_item is None:
                frozen_reference = None
                scope_blockers.append("frozen_candidate_chain_reference_missing")
            else:
                frozen_index, frozen_scope = frozen_item
                frozen_article = frozen_scope["base_treaty"].get("article_number")
                frozen_reference = {
                    "dataset": str(FROZEN_CHAINS.relative_to(ROOT)),
                    "json_path": f"$.scopes[{frozen_index}]",
                    "candidate_sha256": frozen_scope.get("candidate_sha256"),
                    "candidate_chain_complete": frozen_scope.get("candidate_chain_complete"),
                    "verification_status": frozen_scope.get("verification_status"),
                    "legacy_article_number": frozen_article,
                    "reference_only": True,
                }
                if article["resolved"] and frozen_article != article["article_number"]:
                    conflict = {
                        "scope_id": scope_id,
                        "legacy_article_number": frozen_article,
                        "treaty_heading_resolved_article_number": article["article_number"],
                    }
                    article_conflicts.append(conflict)
                    scope_blockers.append("frozen_candidate_article_number_conflict")

            if not article["resolved"]:
                scope_blockers.append(f"{income}_article_source_location_not_resolved")
            else:
                resolved_article_count += 1

            domestic_present = scope_present(domestic, country, income)
            if not domestic_present:
                scope_blockers.append("domestic_eu_candidate_reference_missing")

            scopes.append(
                {
                    "scope_id": scope_id,
                    "recipient_country": country,
                    "income_type": income,
                    "treaty_article": article["article_number"],
                    "article_evidence": article,
                    "frozen_candidate_chain_reference": frozen_reference,
                    "domestic_eu_dataset_reference": {
                        "dataset": str(DOMESTIC_EU.relative_to(ROOT)),
                        "scope_reference_present": domestic_present,
                    },
                    "candidate_coverage_status": (
                        "assembled_needs_review"
                        if frozen_reference is not None and article["resolved"]
                        else "evidence_gap_needs_review"
                    ),
                    "review_blockers": sorted(set(scope_blockers)),
                    "verification_status": "needs_review",
                    "stage5_terminal_status": "pending",
                    "human_primary_review_complete": False,
                    "independent_approval_complete": False,
                    "production_releasable": False,
                }
            )

        entries.append(
            {
                "country": country,
                "country_name": partner.get("country"),
                "workflow_class": next(
                    row["workflow_class"]
                    for row in execution["remaining80_operational_inventory"]
                    if row["country"] == country
                ),
                "canonical_treaty_source_resolution": {
                    "status": source_status,
                    "method": resolution_method,
                    "error": source_error,
                    "source": binding,
                },
                "article_evidence": article_map,
                "signature_clause_evidence": {
                    "status": signature_status,
                    "candidate_count": len(signature_candidates),
                    "candidates": signature_candidates[:10],
                    "interpretation_status": "not_assessed_needs_human_review",
                },
                "related_instrument_inventory": related,
                "mli_inventory_candidate": {
                    "mli_listed": bool(partner.get("mli_listed")),
                    "mli_notice_available": bool(partner.get("mli_notice_available")),
                    "effect_interpretation_status": "not_assessed_needs_human_review",
                },
                "entry_into_force_inventory_candidate": partner.get("entry_into_force"),
                "review_blockers": sorted(set(country_blockers)),
                "verification_status": "needs_review",
                "stage5_terminal_status": "pending",
                "human_primary_review_complete": False,
                "independent_approval_complete": False,
                "production_releasable": False,
                "fail_closed": True,
                "scopes": scopes,
            }
        )

    all_scopes = [scope for entry in entries for scope in entry["scopes"]]
    if len(all_scopes) != 210:
        raise RuntimeError(f"Expected 210 remaining scopes, found {len(all_scopes)}")

    frozen_reference_count = sum(
        scope["frozen_candidate_chain_reference"] is not None for scope in all_scopes
    )

    return {
        "schema_version": 1,
        "dataset_release": "stage5-remaining70-candidate-evidence-2026-08-09.1",
        "purpose": (
            "Large-batch, review-only evidence assembly for remaining80 batches 02-08. "
            "It derives article locations from each treaty's own structured headings, "
            "retains frozen candidate chains as references, and records unresolved evidence."
        ),
        "safety_boundary": {
            "candidate_evidence_is_not_legal_verification": True,
            "frozen_remaining_294_is_reference_only": True,
            "automatic_needs_review_promotion_forbidden": True,
            "missing_or_conflicting_evidence_fails_closed": True,
            "no_production_rules_created": True,
        },
        "batch_boundary": {
            "included_batch_ids": [batch["batch_id"] for batch in batches[1:]],
            "excluded_completed_batch_id": batches[0]["batch_id"],
            "countries": remaining70,
            "country_count": 70,
            "scope_count": 210,
        },
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (
                EXECUTION,
                INVENTORY,
                SOURCE_MANIFEST,
                FROZEN_CHAINS,
                DOMESTIC_EU,
                BATCH01_DOSSIER,
            )
        },
        "summary": {
            "country_count": 70,
            "scope_count": 210,
            "frozen_candidate_chain_reference_count": frozen_reference_count,
            "treaty_heading_resolved_article_count": resolved_article_count,
            "treaty_heading_unresolved_article_count": 210 - resolved_article_count,
            "article_number_conflict_count": len(article_conflicts),
            "source_resolution_counts": dict(sorted(source_resolution_counts.items())),
            "signature_clause_status_counts": dict(sorted(signature_status_counts.items())),
            "verified_scope_count": 0,
            "production_releasable_scope_count": 0,
        },
        "article_number_conflicts": article_conflicts,
        "entries": entries,
    }


def build_batch_payloads(
    remaining70_evidence: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    execution = load(EXECUTION)
    entries_by_country = {
        entry["country"]: entry for entry in remaining70_evidence["entries"]
    }
    payloads = {}

    for batch in execution["remaining80_work_batches"][1:]:
        entries = [entries_by_country[country] for country in batch["countries"]]
        relative = (
            OUTPUT_DIR.relative_to(ROOT) / f"{batch['batch_id']}.json"
        ).as_posix()
        payloads[relative] = {
            "schema_version": 1,
            "dataset_release": (
                f"{remaining70_evidence['dataset_release']}-{batch['batch_id']}"
            ),
            "purpose": remaining70_evidence["purpose"],
            "safety_boundary": remaining70_evidence["safety_boundary"],
            "batch": {
                "batch_id": batch["batch_id"],
                "countries": batch["countries"],
                "country_count": 10,
                "scope_count": 30,
            },
            "source_hashes": remaining70_evidence["source_hashes"],
            "entries": entries,
        }

    return payloads


def build_index(
    remaining70_evidence: dict[str, Any],
    batch_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_release": remaining70_evidence["dataset_release"],
        "purpose": remaining70_evidence["purpose"],
        "safety_boundary": remaining70_evidence["safety_boundary"],
        "batch_boundary": remaining70_evidence["batch_boundary"],
        "source_hashes": remaining70_evidence["source_hashes"],
        "summary": remaining70_evidence["summary"],
        "article_number_conflicts": remaining70_evidence["article_number_conflicts"],
        "batch_files": [
            {
                "path": relative,
                "sha256": sha256_bytes(render(payload).encode("utf-8")),
                "batch_id": payload["batch"]["batch_id"],
                "country_count": payload["batch"]["country_count"],
                "scope_count": payload["batch"]["scope_count"],
            }
            for relative, payload in batch_payloads.items()
        ],
    }


def build_coverage(
    remaining70_evidence: dict[str, Any],
    batch_payloads: dict[str, dict[str, Any]],
    index: dict[str, Any],
) -> dict[str, Any]:
    execution = load(EXECUTION)
    frozen = load(FROZEN_CHAINS)
    pilot = load(PILOT_EVIDENCE)
    batch01 = load(BATCH01_DOSSIER)
    migration = load(MIGRATION_BOUNDARY)

    frozen_by_scope = {
        f"CZ-{entry['recipient_country']}-{entry['income_type']}": (index, entry)
        for index, entry in enumerate(frozen["scopes"])
    }
    batch01_scope_paths = {
        scope["scope_id"]: f"$.entries[{entry_index}].scopes[{scope_index}]"
        for entry_index, entry in enumerate(batch01["entries"])
        for scope_index, scope in enumerate(entry["scopes"])
    }
    remaining70_scope_paths = {
        scope["scope_id"]: {
            "dataset": relative,
            "json_path": f"$.entries[{entry_index}].scopes[{scope_index}]",
        }
        for relative, payload in batch_payloads.items()
        for entry_index, entry in enumerate(payload["entries"])
        for scope_index, scope in enumerate(entry["scopes"])
    }

    rows = []
    for scope in execution["scopes"]:
        scope_id = scope["scope_id"]
        country = scope["recipient_country"]
        cohort = scope["cohort"]

        if cohort == "pilot_at_ch":
            if country not in pilot["countries"]:
                raise RuntimeError(f"Pilot candidate evidence missing for {scope_id}")
            candidate_reference = {
                "dataset": str(PILOT_EVIDENCE.relative_to(ROOT)),
                "json_path": f"$.countries.{country}",
                "reference_kind": "pilot_candidate_evidence",
            }
            stage5_reference = candidate_reference
        else:
            frozen_item = frozen_by_scope.get(scope_id)
            if frozen_item is None:
                raise RuntimeError(f"Frozen candidate chain missing for {scope_id}")
            frozen_index, frozen_scope = frozen_item
            candidate_reference = {
                "dataset": str(FROZEN_CHAINS.relative_to(ROOT)),
                "json_path": f"$.scopes[{frozen_index}]",
                "reference_kind": "frozen_remaining_294_candidate_chain",
                "candidate_sha256": frozen_scope.get("candidate_sha256"),
            }

            if scope_id in batch01_scope_paths:
                stage5_reference = {
                    "dataset": str(BATCH01_DOSSIER.relative_to(ROOT)),
                    "json_path": batch01_scope_paths[scope_id],
                    "reference_kind": "batch01_stage5_legal_chain_candidate",
                }
            elif scope_id in remaining70_scope_paths:
                stage5_reference = {
                    **remaining70_scope_paths[scope_id],
                    "reference_kind": "remaining70_stage5_evidence_candidate",
                }
            elif cohort == "final23":
                stage5_reference = {
                    "dataset": str(MIGRATION_BOUNDARY.relative_to(ROOT)),
                    "json_path": "$",
                    "reference_kind": "final23_migration_boundary_and_existing_candidates",
                }
            else:
                raise RuntimeError(f"Stage 5 candidate evidence missing for {scope_id}")

        rows.append(
            {
                "scope_id": scope_id,
                "source_country": "CZ",
                "recipient_country": country,
                "income_type": scope["income_type"],
                "cohort": cohort,
                "candidate_chain_reference": candidate_reference,
                "stage5_evidence_reference": stage5_reference,
                "candidate_coverage_status": "candidate_evidence_present_needs_review",
                "verification_status": "needs_review",
                "stage5_terminal_status": "pending",
                "human_primary_review_complete": False,
                "independent_approval_complete": False,
                "production_releasable": False,
                "fail_closed": True,
            }
        )

    if len(rows) != 300 or len({row["scope_id"] for row in rows}) != 300:
        raise RuntimeError("Stage 5 coverage registry must contain 300 unique scopes")

    return {
        "schema_version": 1,
        "dataset_release": "stage5-candidate-coverage-registry-2026-08-09.1",
        "purpose": (
            "Audit registry proving an explicit candidate evidence reference for all "
            "100 Czech treaty partners and 300 income scopes. Candidate coverage is "
            "not legal verification, human-review completion, or production release."
        ),
        "safety_boundary": {
            "candidate_coverage_is_not_legal_verification": True,
            "frozen_remaining_294_is_reference_only": True,
            "final23_candidates_are_not_modified": True,
            "automatic_needs_review_promotion_forbidden": True,
            "all_scopes_fail_closed": True,
        },
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in (
                EXECUTION,
                FROZEN_CHAINS,
                PILOT_EVIDENCE,
                BATCH01_DOSSIER,
                MIGRATION_BOUNDARY,
            )
        }
        | {
            str(INDEX_OUTPUT.relative_to(ROOT)): sha256_bytes(
                render(index).encode("utf-8")
            ),
            **{
                relative: sha256_bytes(render(payload).encode("utf-8"))
                for relative, payload in batch_payloads.items()
            },
        },
        "coverage": {
            "country_count": len({row["recipient_country"] for row in rows}),
            "scope_count": len(rows),
            "candidate_evidence_present_scope_count": len(rows),
            "human_primary_review_complete_scope_count": 0,
            "independent_approval_complete_scope_count": 0,
            "production_releasable_scope_count": 0,
            "verification_status_counts": {"needs_review": 300},
            "terminal_status_counts": {"pending": 300, "verified": 0, "blocked": 0},
        },
        "scopes": rows,
    }


def main() -> None:
    evidence = build()
    batch_payloads = build_batch_payloads(evidence)
    index = build_index(evidence, batch_payloads)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for relative, payload in batch_payloads.items():
        (ROOT / relative).write_text(render(payload), encoding="utf-8")
    INDEX_OUTPUT.write_text(render(index), encoding="utf-8")
    COVERAGE_OUTPUT.write_text(
        render(build_coverage(evidence, batch_payloads, index)), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
