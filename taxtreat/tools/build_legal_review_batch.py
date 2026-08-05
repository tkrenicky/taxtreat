from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

QUEUE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "remaining_294_review_queue.json"
)
READINESS = (
    ROOT
    / "data"
    / "legal_reviews"
    / "remaining_294_evidence_readiness.json"
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
    / "batches"
    / "batch_01_priority_eu.json"
)

COUNTRIES = (
    "BE",
    "DE",
    "DK",
    "ES",
    "FR",
    "IT",
    "NL",
    "PL",
    "SE",
    "SK",
)

REVIEW_CHECKS = (
    "Confirm applicable Czech domestic-law treatment.",
    "Confirm treaty and all amending protocols.",
    "Confirm MLI application and effective date.",
    "Confirm Article 10 dividend rate conditions.",
    "Confirm Article 11 interest rate and exemptions.",
    "Confirm Article 12 royalty definition and rate.",
    "Confirm beneficial-owner requirement.",
    "Confirm EU directive eligibility where relevant.",
    "Confirm minimum holding and ownership conditions.",
    "Confirm relevant payment-date version of all rules.",
    "Confirm required payer documentation.",
    "Record conclusion and supporting source passages.",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_batch() -> dict[str, Any]:
    queue = read_json(QUEUE)
    readiness = read_json(READINESS)
    artifacts = read_json(ARTIFACTS)

    queue_by_id = {
        packet["packet_id"]: packet
        for packet in queue["packets"]
    }
    artifact_by_source = {
        item["source_id"]: item
        for item in artifacts["artifacts"]
    }

    selected = [
        packet
        for packet in readiness["packets"]
        if packet["recipient_country"] in COUNTRIES
    ]

    if len(selected) != 30:
        raise ValueError(
            f"Expected 30 packets in batch 01, found {len(selected)}."
        )

    if not all(packet["all_sources_bound"] for packet in selected):
        raise ValueError(
            "Batch 01 contains packets without fully bound evidence."
        )

    packets = []

    for ready in sorted(
        selected,
        key=lambda item: (
            COUNTRIES.index(item["recipient_country"]),
            item["income_type"],
        ),
    ):
        queue_packet = queue_by_id[ready["packet_id"]]

        evidence = []

        for source_id in queue_packet["evidence_source_ids"]:
            artifact = artifact_by_source[source_id]

            evidence.append(
                {
                    "source_id": source_id,
                    "sha256": artifact["sha256"],
                    "artifact_status": artifact["status"],
                    "artifact_uri": artifact["artifact_uri"],
                    "official_url": artifact["official_url"],
                    "final_url": artifact["final_url"],
                }
            )

        packet = {
            "packet_id": queue_packet["packet_id"],
            "source_country": queue_packet["source_country"],
            "recipient_country": queue_packet["recipient_country"],
            "recipient_country_name": queue_packet[
                "recipient_country_name"
            ],
            "income_type": queue_packet["income_type"],
            "candidate_sha256": queue_packet["candidate_sha256"],
            "candidate_dataset_releases": queue_packet[
                "candidate_dataset_releases"
            ],
            "evidence": evidence,
            "review_checklist": [
                {
                    "check": check,
                    "status": "pending",
                    "reviewer_note": None,
                    "supporting_source_ids": [],
                }
                for check in REVIEW_CHECKS
            ],
            "proposed_conclusion": None,
            "reviewer_id": None,
            "reviewed_at": None,
            "review_outcome": None,
            "rule_snapshot_ids": [],
            "independent_approval": {
                "approver_id": None,
                "approved_at": None,
                "approval_outcome": None,
            },
            "status": "awaiting_primary_review",
            "promotable_to_active_rules": False,
        }

        packet["batch_packet_sha256"] = stable_hash(packet)
        packets.append(packet)

    payload = {
        "schema_version": 1,
        "dataset_release": "legal-review-batch-01-2026-08-05.1",
        "batch_name": "Priority EU jurisdictions",
        "countries": list(COUNTRIES),
        "summary": {
            "countries": len(COUNTRIES),
            "packets": len(packets),
            "packets_awaiting_primary_review": len(packets),
            "packets_approved": 0,
        },
        "policy": {
            "primary_legal_review_required": True,
            "independent_approval_required": True,
            "fail_closed": True,
            "no_automatic_legal_conclusions": True,
        },
        "packets": packets,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    payload = build_batch()

    print("Legal review batch 01 created.")
    print("Countries:", payload["summary"]["countries"])
    print("Packets:", payload["summary"]["packets"])
    print(
        "Awaiting primary review:",
        payload["summary"]["packets_awaiting_primary_review"],
    )
    print("Output:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
