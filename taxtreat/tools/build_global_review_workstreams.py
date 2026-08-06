from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

PACKS_DIR = GLOBAL_DIR / "packs"

CLASSIFICATION_PATH = (
    GLOBAL_DIR
    / "global_blocker_classification.json"
)

OUTPUT_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams_summary.json"
)


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _has_mli(pack: dict[str, Any]) -> bool:
    layers = pack.get("legal_layers", {})

    if layers.get("mli_effects"):
        return True

    chain = layers.get("instrument_chain") or {}
    mli = chain.get("mli") or {}

    return mli.get("status") not in {
        None,
        "not_listed",
    }


def _has_protocol(pack: dict[str, Any]) -> bool:
    layers = pack.get("legal_layers", {})

    if layers.get("protocol_effect"):
        return True

    chain = layers.get("instrument_chain") or {}
    protocol = chain.get("protocol") or {}

    return bool(
        protocol.get("required")
        or protocol.get("candidate_status")
        not in {
            None,
            "not_listed",
        }
    )


def _has_status_instrument(
    pack: dict[str, Any],
) -> bool:
    chain = (
        pack.get("legal_layers", {})
        .get("instrument_chain")
        or {}
    )

    status = (
        chain.get("treaty_status_instrument")
        or {}
    )

    return status.get("candidate_status") not in {
        None,
        "not_listed",
    }


def _has_eu_relief(
    pack: dict[str, Any],
) -> bool:
    domestic = (
        pack.get("legal_layers", {})
        .get("domestic_and_eu")
        or {}
    )

    return bool(
        domestic.get(
            "relief_eligible_by_jurisdiction"
        )
    )


def _workstreams(
    pack: dict[str, Any],
    classification: dict[str, Any],
) -> list[str]:
    streams = [
        "czech_domestic_rate_review",
        "base_treaty_semantic_review",
        "independent_primary_legal_review",
    ]

    if _has_eu_relief(pack):
        streams.append(
            "eu_or_domestic_relief_review"
        )

    if _has_mli(pack):
        streams.append(
            "mli_ppt_and_effective_date_review"
        )

    if _has_protocol(pack):
        streams.append(
            "protocol_effect_review"
        )

    if _has_status_instrument(pack):
        streams.append(
            "treaty_status_instrument_review"
        )

    if classification[
        "pilot_structure_exception"
    ]:
        streams.append(
            "pilot_structure_reconciliation"
        )

    return streams


def _priority(
    streams: list[str],
) -> str:
    priority = (
        "treaty_status_instrument_review",
        "pilot_structure_reconciliation",
        "protocol_effect_review",
        "mli_ppt_and_effective_date_review",
        "eu_or_domestic_relief_review",
        "base_treaty_semantic_review",
        "czech_domestic_rate_review",
        "independent_primary_legal_review",
    )

    for stream in priority:
        if stream in streams:
            return stream

    raise ValueError(
        "No primary review workstream assigned."
    )


def build_workstreams() -> dict[str, Any]:
    classification = json.loads(
        CLASSIFICATION_PATH.read_text(
            encoding="utf-8"
        )
    )

    classifications = {
        row["packet_id"]: row
        for row in classification["scopes"]
    }

    if len(classifications) != 300:
        raise ValueError(
            "Expected 300 classified scopes."
        )

    rows: list[dict[str, Any]] = []

    for path in sorted(
        PACKS_DIR.glob("*.json")
    ):
        pack = json.loads(
            path.read_text(encoding="utf-8")
        )

        packet_id = pack["packet_id"]

        if packet_id not in classifications:
            raise ValueError(
                f"{packet_id}: classification missing."
            )

        classified = classifications[packet_id]
        streams = _workstreams(
            pack,
            classified,
        )

        row = {
            "packet_id": packet_id,
            "pack_file": path.name,
            "source_country": (
                pack["source_country"]
            ),
            "recipient_country": (
                pack["recipient_country"]
            ),
            "recipient_country_name": (
                pack["recipient_country_name"]
            ),
            "income_type": pack["income_type"],
            "status": pack["status"],
            "candidate_readiness": (
                pack["candidate_readiness"]
            ),
            "approval_eligible": (
                pack["approval_eligible"]
            ),
            "promotable_to_active_rules": (
                pack[
                    "promotable_to_active_rules"
                ]
            ),
            "primary_blocker_category": (
                classified[
                    "primary_blocker_category"
                ]
            ),
            "review_workstreams": streams,
            "primary_review_workstream": (
                _priority(streams)
            ),
            "has_instrument_chain": (
                pack.get("legal_layers", {})
                .get("instrument_chain")
                is not None
            ),
            "has_mli_effect": _has_mli(pack),
            "has_protocol_effect": (
                _has_protocol(pack)
            ),
            "has_status_instrument": (
                _has_status_instrument(pack)
            ),
            "has_eu_or_domestic_relief": (
                _has_eu_relief(pack)
            ),
            "pilot_structure_exception": (
                classified[
                    "pilot_structure_exception"
                ]
            ),
            "review_status": (
                "workstreams_assigned_fail_closed"
            ),
            "review_pack_sha256": (
                pack["review_pack_sha256"]
            ),
            "classification_sha256": (
                classified[
                    "classification_sha256"
                ]
            ),
        }

        row["workstream_sha256"] = (
            _sha256_json(row)
        )

        rows.append(row)

    if len(rows) != 300:
        raise ValueError(
            f"Expected 300 workstream rows, "
            f"found {len(rows)}."
        )

    if len({
        row["packet_id"]
        for row in rows
    }) != 300:
        raise ValueError(
            "Duplicate packet IDs detected."
        )

    if any(
        row["approval_eligible"]
        or row["promotable_to_active_rules"]
        or row["status"]
        != "awaiting_primary_review"
        for row in rows
    ):
        raise ValueError(
            "Workstreams must remain fail-closed."
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-review-workstreams-"
            "2026-08-06.1"
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "policy": {
            "fail_closed": True,
            "workstream_assignment_is_not_legal_approval":
                True,
            "multiple_workstreams_per_scope":
                True,
        },
        "scopes": sorted(
            rows,
            key=lambda row: (
                row["recipient_country"],
                row["income_type"],
            ),
        ),
    }


def build_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    rows = payload["scopes"]

    stream_counts = Counter(
        stream
        for row in rows
        for stream in row[
            "review_workstreams"
        ]
    )

    primary_counts = Counter(
        row["primary_review_workstream"]
        for row in rows
    )

    return {
        "schema_version": 1,
        "dataset_release": (
            payload["dataset_release"]
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "workstream_counts": dict(
            sorted(stream_counts.items())
        ),
        "primary_workstream_counts": dict(
            sorted(primary_counts.items())
        ),
        "mli_scope_count": sum(
            row["has_mli_effect"]
            for row in rows
        ),
        "protocol_scope_count": sum(
            row["has_protocol_effect"]
            for row in rows
        ),
        "status_instrument_scope_count": sum(
            row["has_status_instrument"]
            for row in rows
        ),
        "eu_or_domestic_relief_scope_count": sum(
            row["has_eu_or_domestic_relief"]
            for row in rows
        ),
        "pilot_structure_scope_count": sum(
            row["pilot_structure_exception"]
            for row in rows
        ),
        "approval_eligible_scopes": 0,
        "promotable_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_workstreams()
    summary = build_summary(payload)

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Scopes:", payload["scope_count"])
    print("Countries:", payload["country_count"])
    print(
        "Workstreams:",
        summary["workstream_counts"],
    )
    print(
        "Primary workstreams:",
        summary[
            "primary_workstream_counts"
        ],
    )


if __name__ == "__main__":
    main()
