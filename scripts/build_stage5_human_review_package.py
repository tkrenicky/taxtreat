from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_stage5_batch01_legal_chain_dossier import income_article_evidence  # noqa: E402


BASE = ROOT / "data/legal_reviews/global_cz_outbound"
PACKS = BASE / "packs"
OUTPUT_DIR = BASE / "stage5_human_review_package"
INDEX_OUTPUT = OUTPUT_DIR / "index.json"
BLOCKERS_OUTPUT = BASE / "stage5_global_blocker_registry.json"
MANIFEST = ROOT / "data/manifests/source_manifest.json"
INVENTORY = ROOT / "data/legal_consolidation/mf_inventory.json"
FROZEN = ROOT / "data/legal_consolidation/remaining_294_instrument_chains.json"
EXECUTION = ROOT / "data/legal_consolidation/stage5_execution_manifest.json"
FINAL23_LANGUAGE = BASE / "final23_language_authority_verification.json"
BATCH01_LANGUAGE = BASE / "stage5_remaining80_batch_01_language_authority_evidence.json"
REMAINING70_INDEX = BASE / "stage5_remaining70_candidate_evidence/index.json"
REMEDIATION = BASE / "stage5_language_authority_remediation.json"
FINAL10 = BASE / "stage5_final10_source_remediation.json"
INCOMES = ("dividend", "interest", "royalty")


def load(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(f"Required file missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_remaining70() -> dict[str, dict[str, Any]]:
    index = load(REMAINING70_INDEX)
    return {
        row["country"]: row
        for node in index["batch_files"]
        for row in load(ROOT / node["path"])["entries"]
    }


def language_map() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    final23 = load(FINAL23_LANGUAGE)
    for record in final23["records"]:
        country = record["treaty_pair_id"].split("-")[1]
        complete = record["language_authority_complete"] is True
        rows[country] = {
            "evidence_class": "existing_repository_language_record",
            "evidence": record,
            "machine_evidence_located": complete,
            "source_remediation_required": not complete,
            "blockers": [] if complete else ["language_authority_primary_source_remediation_required"],
        }

    for record in load(BATCH01_LANGUAGE)["entries"]:
        rows[record["country"]] = {
            "evidence_class": "official_source_candidate_evidence",
            "evidence": record,
            "machine_evidence_located": True,
            "source_remediation_required": False,
            "blockers": [],
        }

    for country, record in load_remaining70().items():
        clause = record["signature_clause_evidence"]
        located = clause["candidate_count"] > 0
        rows[country] = {
            "evidence_class": "hash_bound_repository_signature_clause_candidate",
            "evidence": clause,
            "machine_evidence_located": located,
            "source_remediation_required": not located,
            "blockers": [] if located else ["language_authority_primary_source_remediation_required"],
        }

    for record in load(REMEDIATION)["entries"]:
        rows[record["country"]] = {
            "evidence_class": "current_official_pdf_signature_clause_candidate",
            "evidence": record,
            "machine_evidence_located": True,
            "source_remediation_required": False,
            "blockers": [],
        }

    for country in ("AT", "CH"):
        rows[country] = {
            "evidence_class": "explicit_blocker",
            "evidence": None,
            "machine_evidence_located": False,
            "source_remediation_required": True,
            "blockers": ["language_authority_primary_source_remediation_required"],
        }
    if FINAL10.is_file():
        for record in load(FINAL10)["language_authority_entries"]:
            rows[record["country"]] = {
                "evidence_class": "current_official_pdf_signature_clause_candidate",
                "evidence": record,
                "machine_evidence_located": True,
                "source_remediation_required": False,
                "blockers": [],
            }
    return rows


def build() -> dict[str, Any]:
    execution = load(EXECUTION)
    for relative, expected in execution["frozen_remaining_294_hashes"].items():
        if digest(ROOT / relative) != expected:
            raise RuntimeError(f"Frozen remaining_294 hash changed: {relative}")

    manifest = {row["source_id"]: row for row in load(MANIFEST)["sources"]}
    partners = {row["iso2"]: row for row in load(INVENTORY)["partners"]}
    frozen = {f"CZ-{row['recipient_country']}-{row['income_type']}": row for row in load(FROZEN)["scopes"]}
    languages = language_map()
    final10_chains = {
        row["country"]: row
        for row in load(FINAL10)["instrument_chain_entries"]
    }
    pack_paths = sorted(PACKS.glob("cz-*-legal-review.json"))
    packs = [load(path) | {"_path": str(path.relative_to(ROOT))} for path in pack_paths]
    if len(packs) != 300:
        raise RuntimeError(f"Expected 300 existing scope packs, found {len(packs)}")

    scopes = []
    for pack in sorted(packs, key=lambda p: (p["recipient_country"], INCOMES.index(p["income_type"]))):
        country = pack["recipient_country"]
        income = pack["income_type"]
        scope_id = f"CZ-{country}-{income}"
        chain = pack["legal_layers"]["instrument_chain"]
        if chain is None:
            consolidated = final10_chains[country]
            source_id = consolidated["base_treaty"]["manifest_source_id"]
            base_article = income_article_evidence(load(ROOT / manifest[source_id]["parsed_path"]), income)
            mli_effect = consolidated["mli"]["candidate_effect_record"]
            chain = {
                "base_treaty": {
                    "source_id": source_id,
                    "article_number": base_article["article_number"],
                    "article_text_sha256": hashlib.sha256(base_article["evidence"][0]["excerpt"].encode("utf-8")).hexdigest(),
                    "risk_flags": [],
                },
                "instrument_inventory": {
                    "entry_into_force": partners[country]["entry_into_force"],
                },
                "protocol": {
                    "candidate_status": "official_protocol_relationship_evidence_located_needs_human_review",
                    "candidate_effective_from": None,
                    "required": True,
                    "source_ids": [consolidated["protocol"]["inventory"]["source_id"]],
                    "official_primary_evidence": consolidated["protocol"],
                },
                "mli": {
                    "status": "official_matching_and_withholding_effect_candidate_needs_human_review",
                    "effective_from": mli_effect["effective_from"],
                    "effect_id": mli_effect["effect_id"],
                    "resolution_source_ids": [consolidated["mli"]["inventory"]["source_id"]],
                    "official_primary_evidence": consolidated["mli"],
                },
                "treaty_status_instrument": {
                    "candidate_status": "official_correction_inventory_reconciled_needs_human_review",
                    "effect_kind": "correction_inventory_candidate",
                    "source_id": consolidated["correction_status_instrument"]["source_id"],
                    "effective_from": None,
                    "effective_to": None,
                },
                "hard_blockers": [],
                "legal_review_tasks": ["base_treaty_candidate_review", "protocol_effect_review", "mli_effect_review", "domestic_rate_candidate_review", "independent_legal_review"],
                "candidate_sha256": consolidated["candidate_sha256"],
            }
        else:
            source_id = chain["base_treaty"]["source_id"]
        source = manifest[source_id]
        parsed_path = ROOT / source["parsed_path"]
        parsed = load(parsed_path)
        article = income_article_evidence(parsed, income)
        if not article["resolved"] or article["evidence_count"] != 1:
            raise RuntimeError(f"Treaty-specific article unresolved for {scope_id}")
        if article["article_number"] != chain["base_treaty"]["article_number"]:
            raise RuntimeError(f"Treaty article conflict for {scope_id}")

        language = languages[country]
        classification = (
            "source_remediation_required"
            if language["source_remediation_required"]
            else "mechanically_complete_ready_for_human_review"
        )
        instrument = chain["instrument_inventory"]
        protocol = chain["protocol"]
        mli = chain["mli"]
        status = chain["treaty_status_instrument"]
        source_remediation_blockers = list(language["blockers"])
        if "instrument_chain_consolidation_required" in chain.get("hard_blockers", []):
            source_remediation_blockers.append("instrument_chain_consolidation_required")
        unresolved = list(dict.fromkeys(
            language["blockers"]
            + chain.get("hard_blockers", [])
            + chain.get("legal_review_tasks", [])
            + chain["base_treaty"].get("risk_flags", [])
            + [
                "confirm_treaty_text_and_article_interpretation",
                "confirm_protocol_status_scope_and_effect",
                "confirm_treaty_status_and_withholding_effective_dates",
                "confirm_mli_matching_reservations_and_effect",
                "confirm_domestic_czech_wht_and_any_eu_relief",
                "independent_four_eyes_approval_required",
            ]
        ))
        frozen_row = frozen.get(scope_id)
        scopes.append({
            "scope_id": scope_id,
            "source_country": "CZ",
            "recipient_country": country,
            "recipient_country_name": pack["recipient_country_name"],
            "income_type": income,
            "blocker_partition": classification,
            "source_remediation_blockers": source_remediation_blockers,
            "canonical_treaty": {
                "source_id": source_id,
                "title": source["source_title"],
                "authority_class": source["authority_class"],
                "official_urls": source.get("official_urls", []),
                "archived_artifact_uri": source.get("artifact_uri"),
                "archived_manifest_sha256": source.get("sha256"),
                "parsed_path": source["parsed_path"],
                "parsed_sha256": digest(parsed_path),
            },
            "treaty_article": {
                "article_number": article["article_number"],
                "heading": article["evidence"][0]["heading"],
                "exact_candidate_excerpt": article["evidence"][0]["excerpt"],
                "json_path": article["evidence"][0]["json_path"],
                "resolution_method": article["evidence"][0]["resolution_method"],
                "article_text_sha256": chain["base_treaty"]["article_text_sha256"],
            },
            "protocol_overlays": {
                "inventory_protocol_listed": partners[country]["protocol_listed"],
                "inventory_related_instruments": partners[country]["related_instruments"],
                "candidate_effect": protocol,
            },
            "treaty_status_instruments": status,
            "mli_evidence": {
                "inventory_mli_listed": partners[country]["mli_listed"],
                "inventory_mli_notice_available": partners[country]["mli_notice_available"],
                "candidate_effect": mli,
                "candidate_effect_records": pack["legal_layers"]["mli_effects"],
            },
            "effective_date_evidence": {
                "inventory_entry_into_force_candidate": instrument["entry_into_force"],
                "protocol_candidate_effective_from": protocol.get("candidate_effective_from"),
                "status_candidate_effective_from": status.get("effective_from"),
                "status_candidate_effective_to": status.get("effective_to"),
                "mli_candidate_effective_from": mli.get("effective_from"),
                "interpretation_status": "not_assessed_needs_human_review",
            },
            "language_authority_evidence": language,
            "domestic_czech_wht_layer": pack["legal_layers"]["domestic_and_eu"]["domestic_rate_candidate"],
            "eu_directive_layer": {
                "potentially_relevant_by_recipient_jurisdiction": pack["legal_layers"]["domestic_and_eu"]["relief_eligible_by_jurisdiction"],
                "candidate": pack["legal_layers"]["domestic_and_eu"]["relief_candidate"],
                "candidate_status": pack["legal_layers"]["domestic_and_eu"]["relief_candidate_status"],
            },
            "unresolved_legal_questions": unresolved,
            "provenance": {
                "existing_review_pack": pack["_path"],
                "existing_review_pack_sha256": digest(ROOT / pack["_path"]),
                "candidate_chain_sha256": chain["candidate_sha256"],
                "frozen_remaining_294_reference": None if frozen_row is None else {"candidate_sha256": frozen_row["candidate_sha256"], "reference_only": True},
            },
            "candidate_status": {
                "verification_status": "needs_review",
                "stage5_terminal_status": "pending",
                "fail_closed": True,
                "production_releasable": False,
            },
            "future_human_review_checklist": {
                "primary_reviewer_id": None,
                "primary_reviewed_at": None,
                "primary_review_complete": False,
                "primary_legal_conclusion": None,
                "independent_approver_id": None,
                "independent_approved_at": None,
                "independent_approval_complete": False,
                "approval_conclusion": None,
            },
        })

    countries = {row["recipient_country"] for row in scopes}
    if len(scopes) != 300 or len(countries) != 100:
        raise RuntimeError("Global scope boundary did not reconcile to 100/300")
    counts = Counter(row["blocker_partition"] for row in scopes)
    counts.setdefault("mechanically_complete_ready_for_human_review", 0)
    counts.setdefault("source_remediation_required", 0)
    counts.setdefault("genuine_legal_ambiguity_requires_human_determination", 0)
    return {"schema_version": 1, "dataset_release": "stage5-human-review-package-2026-08-09.1", "purpose": "Complete candidate dossier queue for human primary review and independent approval. It contains no new human review or production rule.", "safety_boundary": {"all_scopes_needs_review": True, "all_scopes_pending": True, "all_scopes_fail_closed": True, "automatic_verification_or_release_forbidden": True}, "summary": {"country_count": len(countries), "scope_count": len(scopes), "partition_counts": dict(sorted(counts.items()))}, "scopes": scopes}


def write_outputs(data: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for index in range(10):
        rows = data["scopes"][index * 30:(index + 1) * 30]
        path = OUTPUT_DIR / f"batch_{index + 1:02d}.json"
        payload = {key: value for key, value in data.items() if key != "scopes"} | {"batch_id": f"stage5-human-review-{index + 1:02d}", "scopes": rows}
        path.write_text(render(payload), encoding="utf-8")
        files.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path), "country_count": len({r["recipient_country"] for r in rows}), "scope_count": len(rows)})
    index = {key: value for key, value in data.items() if key != "scopes"} | {"batch_files": files}
    INDEX_OUTPUT.write_text(render(index), encoding="utf-8")
    registry_rows = [{"scope_id": r["scope_id"], "recipient_country": r["recipient_country"], "income_type": r["income_type"], "partition": r["blocker_partition"], "blockers": r["source_remediation_blockers"]} for r in data["scopes"]]
    registry = {"schema_version": 1, "dataset_release": "stage5-global-blocker-registry-2026-08-09.1", "partition_definitions": {"mechanically_complete_ready_for_human_review": "All required machine evidence slots are populated; legal review and four-eyes approval remain mandatory.", "source_remediation_required": "At least one required official-source evidence slot remains unresolved.", "genuine_legal_ambiguity_requires_human_determination": "Sources are present but a documented conflict or ambiguity cannot be resolved mechanically."}, "summary": data["summary"], "scopes": registry_rows}
    BLOCKERS_OUTPUT.write_text(render(registry), encoding="utf-8")


def main() -> None:
    write_outputs(build())


if __name__ == "__main__":
    main()
