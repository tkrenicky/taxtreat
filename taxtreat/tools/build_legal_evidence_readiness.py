from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

QUEUE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "remaining_294_review_queue.json"
)
ARTIFACTS = (
    ROOT
    / "data"
    / "manifests"
    / "legal_evidence_artifacts.json"
)
OUTPUT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "remaining_294_evidence_readiness.json"
)

VERIFIED_STATUSES = {
    "existing_verified_artifact",
    "verified_pdf",
    "verified_html",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _stable_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def build_legal_evidence_readiness() -> dict[str, Any]:
    queue = _read_json(QUEUE)
    artifacts_manifest = _read_json(ARTIFACTS)

    if len(queue.get("packets", [])) != 294:
        raise ValueError("Expected 294 legal-review packets.")

    artifact_by_source = {
        item["source_id"]: item
        for item in artifacts_manifest["artifacts"]
    }

    packet_records: list[dict[str, Any]] = []

    for packet in queue["packets"]:
        source_ids = packet["evidence_source_ids"]

        verified_hashes: dict[str, str] = {}
        unresolved_source_ids: list[str] = []
        missing_manifest_source_ids: list[str] = []

        for source_id in source_ids:
            artifact = artifact_by_source.get(source_id)

            if artifact is None:
                missing_manifest_source_ids.append(source_id)
                continue

            digest = artifact.get("sha256")

            if (
                artifact.get("status") in VERIFIED_STATUSES
                and isinstance(digest, str)
                and len(digest) == 64
            ):
                verified_hashes[source_id] = digest
            else:
                unresolved_source_ids.append(source_id)

        all_sources_bound = (
            len(verified_hashes) == len(source_ids)
            and not unresolved_source_ids
            and not missing_manifest_source_ids
        )

        record = {
            "packet_id": packet["packet_id"],
            "source_country": packet["source_country"],
            "recipient_country": packet["recipient_country"],
            "income_type": packet["income_type"],
            "required_evidence_source_ids": source_ids,
            "verified_evidence_artifact_hashes": verified_hashes,
            "unresolved_evidence_source_ids": sorted(
                unresolved_source_ids
            ),
            "missing_manifest_source_ids": sorted(
                missing_manifest_source_ids
            ),
            "all_sources_bound": all_sources_bound,
            "legal_review_status": packet["packet_status"],
            "rule_snapshot_ids": packet["rule_snapshot_ids"],
            "approval_eligible": packet["approval_eligible"],
            "promotable_to_active_rules": (
                packet["promotable_to_active_rules"]
            ),
        }

        record["readiness_sha256"] = _stable_sha256(record)
        packet_records.append(record)

    counts = Counter(
        "all_sources_bound"
        if packet["all_sources_bound"]
        else "blocked_by_unresolved_evidence"
        for packet in packet_records
    )

    unresolved_usage = Counter(
        source_id
        for packet in packet_records
        for source_id in packet["unresolved_evidence_source_ids"]
    )

    payload = {
        "schema_version": 1,
        "dataset_release": (
            "remaining-294-evidence-readiness-2026-08-05.1"
        ),
        "source_review_queue_release": queue["dataset_release"],
        "source_artifact_manifest_release": (
            artifacts_manifest["dataset_release"]
        ),
        "policy": {
            "purpose": (
                "Pre-review evidence binding only; this file does not "
                "constitute legal review, rule snapshots, approval, or "
                "promotion to active rules."
            ),
            "fail_closed": True,
            "queue_packets_are_not_modified": True,
        },
        "summary": {
            "total_packets": len(packet_records),
            "packets_with_all_sources_bound": counts[
                "all_sources_bound"
            ],
            "packets_blocked_by_unresolved_evidence": counts[
                "blocked_by_unresolved_evidence"
            ],
            "unique_unresolved_sources": len(unresolved_usage),
            "unresolved_evidence_references": sum(
                unresolved_usage.values()
            ),
        },
        "unresolved_source_usage": [
            {
                "source_id": source_id,
                "affected_packets": count,
            }
            for source_id, count in sorted(
                unresolved_usage.items()
            )
        ],
        "packets": sorted(
            packet_records,
            key=lambda item: item["packet_id"],
        ),
    }

    if payload["summary"]["unique_unresolved_sources"] != 25:
        raise ValueError(
            "Expected exactly 25 unresolved evidence sources."
        )

    _write_json(OUTPUT, payload)
    return payload


def main() -> None:
    payload = build_legal_evidence_readiness()

    print("Legal evidence readiness map created.")

    for key, value in payload["summary"].items():
        print(f"{key}: {value}")

    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
