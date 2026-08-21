from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

INSTRUMENTS_PATH = SK_DIR / "treaty_instrument_inventory.json"
STATUS_PATH = SK_DIR / "mli_relationship_status_inventory.json"
VERIFIED_PATH = SK_DIR / "mli_pair_specific_verified.json"
OUTPUT_PATH = SK_DIR / "mli_instrument_chain_reconciliation.json"
SUMMARY_PATH = SK_DIR / "mli_instrument_chain_reconciliation_summary.json"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_reconciliation() -> dict[str, Any]:
    instruments = _load(INSTRUMENTS_PATH)
    status = _load(STATUS_PATH)
    verified = _load(VERIFIED_PATH)

    instrument_mli = {
        row["recipient_country"]: row
        for row in instruments["relationships"]
        if row["mli_listed_modified"]
    }
    current = {
        row["recipient_country"]: row
        for row in status["relationships"]
    }
    verified_by_country = {
        row["recipient_country"]: row
        for row in verified["relationships"]
    }

    if len(instrument_mli) != 46 or len(current) != 46:
        raise ValueError("Expected 46 MLI relationships in both inventories.")
    if set(instrument_mli) != set(current):
        raise ValueError("MLI relationship country universes do not match.")

    rows: list[dict[str, Any]] = []
    for country in sorted(current):
        old_notice = instrument_mli[country].get("mli_notice")
        current_notice = current[country]["slovak_notice"]

        if old_notice == current_notice:
            resolution = "aligned_current_notice"
            resolved = True
            evidence = None
        else:
            evidence = verified_by_country.get(country)
            superseded = set((evidence or {}).get("superseded_notices", []))
            verified_current = (evidence or {}).get("current_slovak_notice")
            if old_notice in superseded and verified_current == current_notice:
                resolution = "supersession_verified"
                resolved = True
            else:
                resolution = "notice_mismatch_unresolved"
                resolved = False

        rows.append({
            "recipient_country": country,
            "instrument_inventory_notice": old_notice,
            "current_mf_status_notice": current_notice,
            "notice_alignment_status": resolution,
            "resolved": resolved,
            "supersession_evidence_notice": (
                evidence.get("current_slovak_notice") if evidence else None
            ),
            "human_review_status": "not_started",
            "runtime_release": False,
        })

    return {
        "schema_version": 1,
        "dataset_release": "sk-mli-instrument-chain-reconciliation-2026-08-19.1",
        "source_country": "SK",
        "relationship_count": 46,
        "policy": {
            "notice_mismatch_requires_evidence": True,
            "superseded_notice_must_not_be_treated_as_current": True,
            "unresolved_mismatch_blocks_review_readiness": True,
            "runtime_release": False,
        },
        "relationships": rows,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["relationships"]
    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "relationship_count": len(rows),
        "aligned_current_notice": sum(
            row["notice_alignment_status"] == "aligned_current_notice"
            for row in rows
        ),
        "supersession_verified": sum(
            row["notice_alignment_status"] == "supersession_verified"
            for row in rows
        ),
        "unresolved_notice_mismatches": sum(
            row["notice_alignment_status"] == "notice_mismatch_unresolved"
            for row in rows
        ),
        "resolved_relationships": sum(row["resolved"] for row in rows),
        "fail_closed": True,
    }


def main() -> None:
    payload = build_reconciliation()
    summary = build_summary(payload)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
