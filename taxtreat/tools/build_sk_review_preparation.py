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
MLI_PROFILE_PATH = SK_DIR / "mli_wht_relevance_profile.json"
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
    if row["has_mli_effect"]:
        return "mli_pair_specific_substantive_review"
    return "base_treaty_semantic_review"


def _mli_result_changing_articles(
    profile: dict[str, Any],
    income_type: str,
) -> list[str]:
    rows = []
    for article, detail in profile["articles"].items():
        if (
            detail.get("can_change_result") is True
            and income_type in detail.get("income_types", [])
        ):
            rows.append(article)
    return sorted(rows, key=int)


def _build_scope(
    relationship: dict[str, Any],
    income_type: str,
    mli_profile: dict[str, Any],
) -> dict[str, Any]:
    recipient = relationship["recipient_country"]
    has_mli_effect = relationship["mli_listed_modified"]
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

    if has_mli_effect:
        workstreams.extend([
            "mli_pair_specific_substantive_review",
            "mli_wht_effective_date_review",
        ])

    for reason in relationship["risk_reasons"]:
        workstream = RISK_WORKSTREAMS.get(reason)
        if workstream and workstream not in workstreams:
            workstreams.append(workstream)

    article = {"dividend": 10, "interest": 11, "royalty": 12}[income_type]
    blockers = [
        "official_primary_treaty_text_not_ingested",
        f"article_{article}_semantic_extraction_pending",
    ]

    mli_result_changing_articles: list[str] = []
    if has_mli_effect:
        mli_result_changing_articles = _mli_result_changing_articles(
            mli_profile,
            income_type,
        )
        blockers.extend([
            "pair_specific_mli_substantive_article_matching_pending",
            "pair_specific_mli_wht_effective_date_pending",
        ])

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
        "has_mli_effect": has_mli_effect,
        "mli_review": {
            "match_status": (
                "pending_pair_specific_notice_review"
                if has_mli_effect
                else "not_mli_listed_modified"
            ),
            "candidate_result_changing_articles": (
                mli_result_changing_articles
            ),
            "ppt_only_assumption_allowed": False,
            "wht_effective_date_status": (
                "pending_pair_specific_notice_review"
                if has_mli_effect
                else "not_applicable"
            ),
        },
        "has_eu_or_domestic_relief": has_eu_relief,
        "risk_tier": relationship["risk_tier"],
        "risk_tier_status": (
            "provisional_instrument_complexity_only_mli_matching_pending"
            if has_mli_effect
            else "instrument_complexity_classified"
        ),
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
    mli_profile = _load(MLI_PROFILE_PATH)
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

    if mli_profile.get("source_country") != "SK":
        raise ValueError("Slovak MLI WHT relevance profile is missing.")
    if mli_profile["policy"].get("pair_specific_matching_required") is not True:
        raise ValueError("Slovak MLI model must require pair-specific matching.")
    if mli_profile["policy"].get("substantive_wht_effect_can_change_result") is not True:
        raise ValueError("Slovak MLI model must preserve substantive WHT effects.")

    required_result_changing = {"3", "4", "7", "8", "10", "12", "13", "14", "15"}
    configured_result_changing = {
        article
        for article, detail in mli_profile["articles"].items()
        if detail.get("can_change_result") is True
    }
    if not required_result_changing.issubset(configured_result_changing):
        raise ValueError("Slovak MLI result-changing article model is incomplete.")

    if domestic.get("status") != "candidate_not_released":
        raise ValueError("Domestic SK WHT model must remain candidate-only.")

    scopes = [
        _build_scope(
            by_country[partner["iso2"]],
            income_type,
            mli_profile,
        )
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
        "schema_version": 2,
        "dataset_release": "sk-machine-review-preparation-2026-08-19.2",
        "source_country": "SK",
        "country_count": 75,
        "scope_count": 225,
        "income_types": list(INCOME_TYPES),
        "policy": {
            "fail_closed": True,
            "mli_is_not_ppt_only": True,
            "mli_pair_specific_substantive_matching_required": True,
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

    mli_pending_countries = {
        row["recipient_country"]
        for row in scopes
        if row["mli_review"]["match_status"]
        == "pending_pair_specific_notice_review"
    }

    return {
        "schema_version": 2,
        "dataset_release": payload["dataset_release"],
        "country_count": 75,
        "scope_count": 225,
        "machine_prepared_scopes": 225,
        "review_ready_scopes": sum(row["review_ready"] for row in scopes),
        "human_reviewed_scopes": 0,
        "production_released_scopes": 0,
        "provisional_instrument_risk_scope_counts": dict(
            sorted(Counter(row["risk_tier"] for row in scopes).items())
        ),
        "provisional_instrument_risk_country_counts": dict(
            sorted(Counter(relationship_risk.values()).items())
        ),
        "mli_relationship_count": len({
            row["recipient_country"]
            for row in scopes
            if row["has_mli_effect"]
        }),
        "mli_scope_count": sum(row["has_mli_effect"] for row in scopes),
        "mli_substantive_matching_pending_relationship_count": (
            len(mli_pending_countries)
        ),
        "mli_substantive_matching_pending_scope_count": sum(
            row["mli_review"]["match_status"]
            == "pending_pair_specific_notice_review"
            for row in scopes
        ),
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
            "First SK human-review sample must be 4 STANDARD + 2 ELEVATED "
            "on provisional instrument-complexity classification."
        )

    return {
        "schema_version": 2,
        "dataset_release": "sk-first-human-review-sample-2026-08-19.2",
        "source_country": "SK",
        "sample_policy": {
            "provisional_standard_scopes": 4,
            "provisional_elevated_scopes": 2,
            "deterministic": True,
            "selection_is_not_legal_approval": True,
            "final_risk_requires_mli_pair_matching": True,
        },
        "review_ready": False,
        "review_blocker": (
            "Primary treaty text, operative Article 10/11/12 wording, and for "
            "MLI-listed relationships pair-specific substantive MLI matching plus "
            "the WHT effective date must be ingested before human legal review starts."
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
    print(
        "Provisional instrument risk countries:",
        summary["provisional_instrument_risk_country_counts"],
    )
    print(
        "Provisional instrument risk scopes:",
        summary["provisional_instrument_risk_scope_counts"],
    )
    print("MLI relationships:", summary["mli_relationship_count"])
    print(
        "MLI substantive matching pending relationships:",
        summary["mli_substantive_matching_pending_relationship_count"],
    )
    print(
        "First human-review sample:",
        [row["packet_id"] for row in sample["sample"]],
    )


if __name__ == "__main__":
    main()
