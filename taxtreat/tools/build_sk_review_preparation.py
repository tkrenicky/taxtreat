from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SK_DIR = ROOT / "data" / "legal_reviews" / "sk_outbound"

PARTNERS_PATH = ROOT / "data" / "sk_treaty_partners.json"
MLI_PATH = ROOT / "data" / "country_sources" / "sk_mli_inventory_source.json"
DOMESTIC_PATH = SK_DIR / "domestic_wht_candidates.json"
INSTRUMENTS_PATH = SK_DIR / "treaty_instrument_inventory.json"

OUTPUT_PATH = SK_DIR / "machine_review_preparation.json"
SUMMARY_PATH = SK_DIR / "machine_review_preparation_summary.json"
SAMPLE_PATH = SK_DIR / "first_human_review_sample.json"

INCOME_TYPES = ("dividend", "interest", "royalty")

EU_MEMBER_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES",
    "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU",
    "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI",
}

RISK_WORKSTREAMS = {
    "protocol_overlay": "protocol_effect_review",
    "correction_notice": "instrument_correction_review",
    "territorial_scope_note": "territorial_scope_review",
    "prevailing_text_feature": "language_and_prevailing_text_review",
    "non_standard_publication": "non_standard_publication_review",
}

SAMPLE_PACKET_IDS = (
    "SK-US-dividend",
    "SK-AT-interest",
    "SK-AU-royalty",
    "SK-NZ-dividend",
    "SK-NL-royalty",
    "SK-GB-interest",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _primary_workstream(row: dict[str, Any]) -> str:
    for reason in row["risk_reasons"]:
        workstream = RISK_WORKSTREAMS.get(reason)
        if workstream:
            return workstream
    return "base_treaty_semantic_review"


def _build_scope(
    relationship: dict[str, Any],
    income_type: str,
) -> dict[str, Any]:
    recipient = relationship["recipient_country"]
    has_eu_relief = (
        recipient in EU_MEMBER_CODES
        and income_type in {"interest", "royalty"}
    )

    workstreams = [
        "slovak_domestic_rule_review",
        "base_treaty_semantic_review",
        "independent_primary_legal_review",
    ]

    if has_eu_relief:
        workstreams.append("eu_or_domestic_relief_review")

    if relationship["mli_listed_modified"]:
        workstreams.append("mli_ppt_and_effective_date_review")

    for reason in relationship["risk_reasons"]:
        workstream = RISK_WORKSTREAMS.get(reason)
        if workstream and workstream not in workstreams:
            workstreams.append(workstream)

    article = {"dividend": 10, "interest": 11, "royalty": 12}[income_type]
    blockers = [
        "official_primary_treaty_text_not_ingested",
        f"article_{article}_semantic_extraction_pending",
    ]

    if relationship["mli_listed_modified"]:
        blockers.append(
            "pair_specific_mli_matching_and_wht_effective_date_pending"
        )

    if has_eu_relief:
        blockers.append(
            "eu_domestic_relief_transaction_conditions_pending_review"
        )

    row = {
        "packet_id": f"SK-{recipient}-{income_type}",
        "source_country": "SK",
        "recipient_country": recipient,
        "recipient_country_name": relationship["recipient_country_name"],
        "income_type": income_type,
        "treaty_publication": relationship["treaty_publication"],
        "treaty_valid_from": relationship["treaty_valid_from"],
        "mli_notice": relationship["mli_notice"],
        "has_mli_effect": relationship["mli_listed_modified"],
        "has_eu_or_domestic_relief": has_eu_relief,
        "risk_tier": relationship["risk_tier"],
        "risk_reasons": relationship["risk_reasons"],
        "review_workstreams": workstreams,
        "primary_review_workstream": "",
        "machine_preparation_status": "inventory_ready_treaty_text_pending",
        "review_ready": False,
        "human_review_status": "not_started",
        "approval_eligible": False,
        "promotable_to_active_rules": False,
        "runtime_status": "not_released",
        "release_blockers": blockers,
    }
    row["primary_review_workstream"] = _primary_workstream(row)
    row["scope_sha256"] = _sha256_json(row)
    return row


def build_machine_preparation() -> dict[str, Any]:
    partners = _load(PARTNERS_PATH)
    mli = _load(MLI_PATH)
    domestic = _load(DOMESTIC_PATH)
    instruments = _load(INSTRUMENTS_PATH)

    if len(partners) != 75:
        raise ValueError(f"Expected 75 SK treaty partners, found {len(partners)}.")

    relationship_rows = instruments["relationships"]
    if len(relationship_rows) != 75:
        raise ValueError(
            "Treaty instrument inventory must contain 75 relationships."
        )

    by_country = {
        row["recipient_country"]: row
        for row in relationship_rows
    }
    if len(by_country) != 75:
        raise ValueError("Duplicate treaty relationship country codes detected.")

    partner_codes = {row["iso2"] for row in partners}
    if partner_codes != set(by_country):
        raise ValueError(
            "Treaty partner list and instrument inventory are not aligned."
        )

    mli_codes = set(mli["covered_partner_codes"])
    inventory_mli_codes = {
        row["recipient_country"]
        for row in relationship_rows
        if row["mli_listed_modified"]
    }
    if len(mli_codes) != 46 or mli_codes != inventory_mli_codes:
        raise ValueError(
            "MLI inventory and treaty instrument inventory are not aligned."
        )

    if domestic.get("status") != "candidate_not_released":
        raise ValueError("Domestic SK WHT model must remain candidate-only.")

    scopes = [
        _build_scope(by_country[partner["iso2"]], income_type)
        for partner in partners
        for income_type in INCOME_TYPES
    ]

    if len(scopes) != 225:
        raise ValueError(f"Expected 225 SK scopes, found {len(scopes)}.")

    if len({row["packet_id"] for row in scopes}) != 225:
        raise ValueError("Duplicate SK packet IDs detected.")

    if any(
        row["review_ready"]
        or row["approval_eligible"]
        or row["promotable_to_active_rules"]
        or row["runtime_status"] != "not_released"
        for row in scopes
    ):
        raise ValueError("SK machine preparation must remain fail-closed.")

    return {
        "schema_version": 1,
        "dataset_release": "sk-machine-review-preparation-2026-08-19.1",
        "source_country": "SK",
        "country_count": 75,
        "scope_count": 225,
        "income_types": list(INCOME_TYPES),
        "policy": {
            "fail_closed": True,
            "mli_ppt_alone_does_not_elevate_risk": True,
            "machine_preparation_is_not_human_approval": True,
            "runtime_release": False,
        },
        "scopes": scopes,
    }


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    scopes = payload["scopes"]
    relationship_risk = {}
    for row in scopes:
        relationship_risk[row["recipient_country"]] = row["risk_tier"]

    return {
        "schema_version": 1,
        "dataset_release": payload["dataset_release"],
        "country_count": 75,
        "scope_count": 225,
        "machine_prepared_scopes": 225,
        "review_ready_scopes": sum(row["review_ready"] for row in scopes),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "risk_scope_counts": dict(
            sorted(Counter(row["risk_tier"] for row in scopes).items())
        ),
        "risk_country_counts": dict(
            sorted(Counter(relationship_risk.values()).items())
        ),
        "mli_relationship_count": len({
            row["recipient_country"]
            for row in scopes
            if row["has_mli_effect"]
        }),
        "mli_scope_count": sum(row["has_mli_effect"] for row in scopes),
        "eu_or_domestic_relief_scope_count": sum(
            row["has_eu_or_domestic_relief"] for row in scopes
        ),
        "fail_closed": True,
    }


def build_first_human_review_sample(
    payload: dict[str, Any],
) -> dict[str, Any]:
    by_packet = {
        row["packet_id"]: row
        for row in payload["scopes"]
    }

    sample = [by_packet[packet_id] for packet_id in SAMPLE_PACKET_IDS]

    standard_count = sum(
        row["risk_tier"] == "STANDARD"
        for row in sample
    )
    elevated_count = sum(
        row["risk_tier"] == "ELEVATED"
        for row in sample
    )

    if (standard_count, elevated_count) != (4, 2):
        raise ValueError(
            "First SK human-review sample must be 4 STANDARD + 2 ELEVATED."
        )

    return {
        "schema_version": 1,
        "dataset_release": "sk-first-human-review-sample-2026-08-19.1",
        "source_country": "SK",
        "sample_policy": {
            "standard_scopes": 4,
            "elevated_scopes": 2,
            "deterministic": True,
            "selection_is_not_legal_approval": True,
        },
        "review_ready": False,
        "review_blocker": (
            "Primary treaty text and operative Article 10/11/12 wording "
            "must be ingested before human legal review starts."
        ),
        "sample": sample,
    }


def main() -> None:
    payload = build_machine_preparation()
    summary = build_summary(payload)
    sample = build_first_human_review_sample(payload)

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SAMPLE_PATH.write_text(
        json.dumps(sample, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("SK countries:", summary["country_count"])
    print("SK scopes:", summary["scope_count"])
    print("Machine prepared:", summary["machine_prepared_scopes"])
    print("Review ready:", summary["review_ready_scopes"])
    print("Risk countries:", summary["risk_country_counts"])
    print("Risk scopes:", summary["risk_scope_counts"])
    print("MLI relationships:", summary["mli_relationship_count"])
    print(
        "First human-review sample:",
        [row["packet_id"] for row in sample["sample"]],
    )


if __name__ == "__main__":
    main()
