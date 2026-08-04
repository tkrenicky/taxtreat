from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONSOLIDATION_DIR = ROOT / "data" / "legal_consolidation"
REVIEW_DIR = ROOT / "data" / "legal_reviews"
DEFAULT_CHAINS = CONSOLIDATION_DIR / "remaining_294_instrument_chains.json"
DEFAULT_DOMESTIC_EU = CONSOLIDATION_DIR / "cz_domestic_eu_candidates.json"
DEFAULT_DECISIONS = REVIEW_DIR / "remaining_294_decisions.json"
DEFAULT_OUTPUT = REVIEW_DIR / "remaining_294_review_queue.json"

SUPPORTED_INCOME_TYPES = {"dividend", "interest", "royalty"}
REVIEW_OUTCOMES = {"accepted_for_independent_approval", "returned_for_correction"}
APPROVAL_OUTCOMES = {"approved", "rejected"}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _scope_index(
    payload: dict[str, Any],
    *,
    expected_count: int,
    label: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in payload.get("scopes", []):
        key = (row["recipient_country"], row["income_type"])
        if key in result:
            raise ValueError(f"Duplicate {label} scope: {key!r}.")
        result[key] = row
    if len(result) != expected_count:
        raise ValueError(
            f"Expected {expected_count} {label} scopes, found {len(result)}."
        )
    return result


def _decision_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for row in payload.get("decisions", []):
        packet_id = row.get("packet_id")
        if not packet_id:
            raise ValueError("Every legal-review decision requires packet_id.")
        if packet_id in decisions:
            raise ValueError(f"Duplicate legal-review decision: {packet_id}.")
        decisions[packet_id] = row
    return decisions


def _parse_timestamp(value: Any, *, field: str, packet_id: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Review packet {packet_id} requires {field}.")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Review packet {packet_id} has invalid {field}."
        ) from exc


def _packet_id(scope: dict[str, Any]) -> str:
    income_token = {
        "dividend": "DIV",
        "interest": "INT",
        "royalty": "ROY",
    }[scope["income_type"]]
    return f"CZ-{scope['recipient_country']}-{income_token}-LEGAL-REVIEW"


def _evidence_source_ids(
    chain: dict[str, Any],
    domestic_scope: dict[str, Any],
) -> list[str]:
    evidence = {
        *chain["instrument_inventory"]["base_source_ids"],
        *chain["instrument_inventory"]["related_source_ids"],
        chain["base_treaty"]["source_id"],
        *chain["protocol"]["source_ids"],
        *chain["mli"]["resolution_source_ids"],
        chain["czech_domestic_law"]["source_id"],
    }
    evidence.add(chain["mli"].get("source_page_id"))
    evidence.add(chain["treaty_status_instrument"].get("source_id"))
    relief = domestic_scope.get("relief_candidate") or {}
    evidence.add(relief.get("directive_source_id"))
    return sorted(source_id for source_id in evidence if source_id)


def _apply_decision(
    packet: dict[str, Any],
    decision: dict[str, Any] | None,
) -> None:
    if decision is None:
        return

    packet_id = packet["packet_id"]
    if decision.get("candidate_sha256") != packet["candidate_sha256"]:
        raise ValueError(
            f"Review packet {packet_id} decision is bound to a stale candidate hash."
        )

    reviewer_id = decision.get("reviewer_id")
    if not reviewer_id:
        raise ValueError(f"Review packet {packet_id} requires reviewer_id.")
    _parse_timestamp(decision.get("reviewed_at"), field="reviewed_at", packet_id=packet_id)
    review_outcome = decision.get("review_outcome")
    if review_outcome not in REVIEW_OUTCOMES:
        raise ValueError(f"Review packet {packet_id} has invalid review_outcome.")

    packet["reviewer_id"] = reviewer_id
    packet["reviewed_at"] = decision["reviewed_at"]
    packet["review_outcome"] = review_outcome
    if review_outcome == "returned_for_correction":
        forbidden = {
            "approver_id",
            "approved_at",
            "approval_outcome",
        }.intersection(decision)
        if forbidden:
            raise ValueError(
                f"Review packet {packet_id} cannot carry approval fields after return."
            )
        packet["packet_status"] = "returned_for_correction"
        return

    rule_snapshot_ids = decision.get("rule_snapshot_ids", [])
    if len(rule_snapshot_ids) != len(set(rule_snapshot_ids)):
        raise ValueError(f"Review packet {packet_id} has duplicate rule_snapshot_ids.")
    evidence_hashes = decision.get("evidence_artifact_hashes", {})
    if not isinstance(evidence_hashes, dict):
        raise ValueError(
            f"Review packet {packet_id} evidence_artifact_hashes must be an object."
        )
    invalid_hashes = sorted(
        source_id
        for source_id, digest in evidence_hashes.items()
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest)
    )
    if invalid_hashes:
        raise ValueError(
            f"Review packet {packet_id} has invalid evidence artifact hashes."
        )
    packet["rule_snapshot_ids"] = rule_snapshot_ids
    packet["evidence_artifact_hashes"] = evidence_hashes
    packet["source_artifacts_verified"] = set(evidence_hashes) == set(
        packet["evidence_source_ids"]
    )
    packet["approval_eligible"] = bool(
        rule_snapshot_ids and packet["source_artifacts_verified"]
    )
    packet["packet_status"] = (
        "awaiting_independent_approval"
        if packet["approval_eligible"]
        else "primary_review_complete_missing_approval_prerequisites"
    )

    approval_outcome = decision.get("approval_outcome")
    approval_fields_present = any(
        decision.get(field) is not None
        for field in ("approver_id", "approved_at", "approval_outcome")
    )
    if approval_outcome is None:
        if approval_fields_present:
            raise ValueError(
                f"Review packet {packet_id} has incomplete approval fields."
            )
        return
    if approval_outcome not in APPROVAL_OUTCOMES:
        raise ValueError(f"Review packet {packet_id} has invalid approval_outcome.")
    if not packet["approval_eligible"]:
        raise ValueError(
            f"Review packet {packet_id} cannot be approved before rule snapshots "
            "and all evidence artifact hashes are bound."
        )
    approver_id = decision.get("approver_id")
    if not approver_id:
        raise ValueError(f"Review packet {packet_id} requires approver_id.")
    if approver_id == reviewer_id:
        raise ValueError(
            f"Review packet {packet_id} reviewer and approver must be independent."
        )
    _parse_timestamp(decision.get("approved_at"), field="approved_at", packet_id=packet_id)
    packet["approver_id"] = approver_id
    packet["approved_at"] = decision["approved_at"]
    packet["approval_outcome"] = approval_outcome
    packet["packet_status"] = (
        "independently_approved" if approval_outcome == "approved" else "rejected"
    )
    if approval_outcome == "approved":
        packet["verification_status"] = "verified"
        packet["promotable_to_active_rules"] = True


def _packet_sha256(packet: dict[str, Any]) -> str:
    canonical = json.dumps(packet, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_legal_review_queue(
    *,
    chains_path: str | Path = DEFAULT_CHAINS,
    domestic_eu_path: str | Path = DEFAULT_DOMESTIC_EU,
    decisions_path: str | Path = DEFAULT_DECISIONS,
) -> dict[str, Any]:
    chains_payload = _read_json(chains_path)
    chains = _scope_index(
        chains_payload,
        expected_count=294,
        label="instrument-chain",
    )
    domestic_payload = _read_json(domestic_eu_path)
    domestic = _scope_index(
        domestic_payload,
        expected_count=300,
        label="domestic/EU",
    )
    decisions = _decision_index(_read_json(decisions_path))

    if set(chains).difference(domestic):
        raise ValueError("Instrument-chain scopes are missing from domestic/EU data.")

    packets = []
    known_packet_ids = set()
    for key, chain in sorted(chains.items()):
        if chain["income_type"] not in SUPPORTED_INCOME_TYPES:
            raise ValueError(f"Unsupported review income type: {chain['income_type']}.")
        if (
            not chain["candidate_chain_complete"]
            or chain["hard_blockers"]
            or chain["verification_status"] != "needs_review"
            or chain["review_ready"] is not False
        ):
            raise ValueError(
                f"Instrument chain {key!r} is not a complete fail-closed candidate."
            )
        packet_id = _packet_id(chain)
        known_packet_ids.add(packet_id)
        review_tasks = sorted(set(chain["legal_review_tasks"]))
        packet = {
            "packet_id": packet_id,
            "source_country": chain["source_country"],
            "recipient_country": chain["recipient_country"],
            "recipient_country_name": chain["recipient_country_name"],
            "income_type": chain["income_type"],
            "candidate_sha256": chain["candidate_sha256"],
            "candidate_dataset_releases": chain["candidate_dataset_releases"],
            "review_tasks": [
                {"check_id": task, "status": "pending"} for task in review_tasks
            ],
            "evidence_source_ids": _evidence_source_ids(chain, domestic[key]),
            "evidence_artifact_hashes": {},
            "source_artifacts_verified": False,
            "rule_snapshot_ids": [],
            "reviewer_id": None,
            "reviewed_at": None,
            "review_outcome": None,
            "approver_id": None,
            "approved_at": None,
            "approval_outcome": None,
            "separation_of_duties_required": True,
            "approval_eligible": False,
            "packet_status": "awaiting_primary_review",
            "verification_status": "needs_review",
            "promotable_to_active_rules": False,
        }
        _apply_decision(packet, decisions.get(packet_id))
        packet["review_packet_sha256"] = _packet_sha256(packet)
        packets.append(packet)

    unknown_decisions = sorted(set(decisions).difference(known_packet_ids))
    if unknown_decisions:
        raise ValueError(
            "Legal-review decisions reference unknown packets: "
            + ", ".join(unknown_decisions)
        )

    status_counts = {
        status: sum(packet["packet_status"] == status for packet in packets)
        for status in (
            "awaiting_primary_review",
            "primary_review_complete_missing_approval_prerequisites",
            "awaiting_independent_approval",
            "returned_for_correction",
            "independently_approved",
            "rejected",
        )
    }
    return {
        "schema_version": 1,
        "dataset_release": "remaining-294-legal-review-queue-2026-08-04.1",
        "source_dataset_release": chains_payload["dataset_release"],
        "review_policy": {
            "candidate_hash_binding_required": True,
            "complete_evidence_artifact_hashes_required": True,
            "canonical_rule_snapshot_required": True,
            "independent_approver_required": True,
            "candidate_assembly_is_not_legal_approval": True,
        },
        "summary": {
            "total_packets": len(packets),
            **status_counts,
            "approval_eligible_packets": sum(
                packet["approval_eligible"] for packet in packets
            ),
            "verified_packets": sum(
                packet["verification_status"] == "verified" for packet in packets
            ),
            "promotable_packets": sum(
                packet["promotable_to_active_rules"] for packet in packets
            ),
        },
        "packets": packets,
    }


def write_legal_review_queue(
    payload: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
