from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

PACKS_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
    / "packs"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

OUTPUT_CLASSIFICATION = (
    OUTPUT_DIR
    / "global_blocker_classification.json"
)

OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / "global_blocker_summary.json"
)


HARD_STATUS_BLOCKERS = {
    "current_treaty_status_review",
    "post_protocol_status_instrument_consolidation",
}

INSTRUMENT_CHAIN_BLOCKERS = {
    "missing_instrument_chain_or_priority_review_row",
}

PROTOCOL_EFFECTIVE_DATE_BLOCKERS = {
    "protocol_consolidation",
    "protocol_effect_candidate_review",
    "mli_matching_and_effective_date",
}

MLI_BLOCKERS = {
    "mli_effect_candidate_review",
}

DOMESTIC_RELIEF_BLOCKERS = {
    "domestic_rate_candidate_review",
    "domestic_and_eu_relief_consolidation",
    "domestic_and_parent_subsidiary_relief_consolidation",
    "recipient_qualification_fact_review",
    "relief_candidate_review",
    "anti_abuse_determination",
}

TREATY_SEMANTIC_BLOCKERS = {
    "semantic_rate_review",
}

HUMAN_REVIEW_BLOCKERS = {
    "independent_legal_review",
}


PRIMARY_PRIORITY = (
    "hard_legal_status_blocker",
    "instrument_chain_blocker",
    "protocol_or_effective_date_blocker",
    "mli_ppt_review",
    "domestic_or_eu_relief_review",
    "treaty_semantic_review",
    "human_confirmation_only",
)


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _categories(blockers: set[str]) -> list[str]:
    categories: list[str] = []

    if blockers & HARD_STATUS_BLOCKERS:
        categories.append("hard_legal_status_blocker")

    if blockers & INSTRUMENT_CHAIN_BLOCKERS:
        categories.append("instrument_chain_blocker")

    if blockers & PROTOCOL_EFFECTIVE_DATE_BLOCKERS:
        categories.append(
            "protocol_or_effective_date_blocker"
        )

    if blockers & MLI_BLOCKERS:
        categories.append("mli_ppt_review")

    if blockers & DOMESTIC_RELIEF_BLOCKERS:
        categories.append(
            "domestic_or_eu_relief_review"
        )

    if blockers & TREATY_SEMANTIC_BLOCKERS:
        categories.append("treaty_semantic_review")

    substantive = blockers.difference(
        HUMAN_REVIEW_BLOCKERS
    )

    if not substantive and blockers:
        categories.append("human_confirmation_only")

    if not categories:
        raise ValueError(
            "Scope has no recognised blocker category."
        )

    return categories


def _primary_category(
    categories: list[str],
) -> str:
    for category in PRIMARY_PRIORITY:
        if category in categories:
            return category

    raise ValueError(
        "No primary blocker category could be assigned."
    )


def _review_track(
    primary_category: str,
) -> str:
    mapping = {
        "hard_legal_status_blocker":
            "special_status_instrument_review",
        "instrument_chain_blocker":
            "pilot_or_chain_reconciliation",
        "protocol_or_effective_date_blocker":
            "protocol_and_effective_date_review",
        "mli_ppt_review":
            "mli_review",
        "domestic_or_eu_relief_review":
            "domestic_relief_review",
        "treaty_semantic_review":
            "treaty_semantic_review",
        "human_confirmation_only":
            "primary_legal_confirmation",
    }

    return mapping[primary_category]


def classify_pack(
    pack: dict[str, Any],
    *,
    pack_file: str,
) -> dict[str, Any]:
    blockers_raw = pack.get("blockers")

    if not isinstance(blockers_raw, list):
        raise ValueError(
            f"{pack_file}: blockers must be a list."
        )

    blockers = {
        str(blocker)
        for blocker in blockers_raw
    }

    categories = _categories(blockers)
    primary = _primary_category(categories)

    instrument_chain = (
        pack.get("legal_layers", {})
        .get("instrument_chain")
    )

    missing_chain_is_pilot = (
        primary == "instrument_chain_blocker"
        and pack.get("recipient_country")
        in {"AT", "CH"}
    )

    row = {
        "packet_id": pack["packet_id"],
        "pack_file": pack_file,
        "source_country": pack["source_country"],
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
            pack["promotable_to_active_rules"]
        ),
        "blockers": sorted(blockers),
        "blocker_categories": categories,
        "primary_blocker_category": primary,
        "review_track": _review_track(primary),
        "instrument_chain_present": (
            instrument_chain is not None
        ),
        "pilot_structure_exception": (
            missing_chain_is_pilot
        ),
        "requires_special_status_review": (
            "hard_legal_status_blocker"
            in categories
        ),
        "requires_protocol_review": (
            "protocol_or_effective_date_blocker"
            in categories
        ),
        "requires_mli_review": (
            "mli_ppt_review"
            in categories
        ),
        "requires_domestic_or_relief_review": (
            "domestic_or_eu_relief_review"
            in categories
        ),
        "requires_treaty_semantic_review": (
            "treaty_semantic_review"
            in categories
        ),
        "review_pack_sha256": (
            pack["review_pack_sha256"]
        ),
        "classification_status": (
            "classified_fail_closed"
        ),
    }

    row["classification_sha256"] = (
        _sha256_json(row)
    )

    return row


def build_classification() -> dict[str, Any]:
    pack_paths = sorted(
        PACKS_DIR.glob("*.json")
    )

    if len(pack_paths) != 300:
        raise ValueError(
            f"Expected 300 review packs, "
            f"found {len(pack_paths)}."
        )

    rows: list[dict[str, Any]] = []

    for path in pack_paths:
        pack = json.loads(
            path.read_text(encoding="utf-8")
        )

        rows.append(
            classify_pack(
                pack,
                pack_file=path.name,
            )
        )

    scope_keys = {
        (
            row["source_country"],
            row["recipient_country"],
            row["income_type"],
        )
        for row in rows
    }

    if len(scope_keys) != 300:
        raise ValueError(
            "Classification contains duplicate scopes."
        )

    if any(
        row["approval_eligible"]
        or row["promotable_to_active_rules"]
        or row["status"]
        != "awaiting_primary_review"
        for row in rows
    ):
        raise ValueError(
            "Classification must remain fail-closed."
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-cz-outbound-blocker-"
            "classification-2026-08-06.1"
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "classification_policy": {
            "fail_closed": True,
            "classification_is_not_legal_approval":
                True,
            "multiple_categories_allowed": True,
            "primary_category_priority": list(
                PRIMARY_PRIORITY
            ),
            "pilot_structure_exceptions": [
                "CZ-AT-DIV",
                "CZ-AT-INT",
                "CZ-AT-ROY",
                "CZ-CH-DIV",
                "CZ-CH-INT",
                "CZ-CH-ROY",
            ],
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
    classification: dict[str, Any],
) -> dict[str, Any]:
    rows = classification["scopes"]

    primary_counts = Counter(
        row["primary_blocker_category"]
        for row in rows
    )

    category_counts = Counter(
        category
        for row in rows
        for category in row[
            "blocker_categories"
        ]
    )

    track_counts = Counter(
        row["review_track"]
        for row in rows
    )

    country_primary = Counter(
        (
            row["recipient_country"],
            row["primary_blocker_category"],
        )
        for row in rows
    )

    special_status_countries = sorted({
        row["recipient_country"]
        for row in rows
        if row[
            "requires_special_status_review"
        ]
    })

    pilot_exception_scopes = sorted(
        row["packet_id"]
        for row in rows
        if row["pilot_structure_exception"]
    )

    return {
        "schema_version": 1,
        "dataset_release": (
            classification["dataset_release"]
        ),
        "scope_count": len(rows),
        "country_count": len({
            row["recipient_country"]
            for row in rows
        }),
        "primary_category_counts": dict(
            sorted(primary_counts.items())
        ),
        "all_category_counts": dict(
            sorted(category_counts.items())
        ),
        "review_track_counts": dict(
            sorted(track_counts.items())
        ),
        "special_status_countries": (
            special_status_countries
        ),
        "pilot_structure_exception_scopes": (
            pilot_exception_scopes
        ),
        "country_primary_category_counts": [
            {
                "recipient_country": country,
                "primary_blocker_category":
                    category,
                "scope_count": count,
            }
            for (
                country,
                category,
            ), count in sorted(
                country_primary.items()
            )
        ],
        "fail_closed": True,
        "approval_eligible_scopes": 0,
        "promotable_scopes": 0,
    }


def write_outputs(
    classification: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_CLASSIFICATION.write_text(
        json.dumps(
            classification,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    OUTPUT_SUMMARY.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    classification = build_classification()
    summary = build_summary(classification)

    write_outputs(
        classification,
        summary,
    )

    print(
        "Classified scopes:",
        classification["scope_count"],
    )

    print(
        "Countries:",
        classification["country_count"],
    )

    print("Primary categories:")

    for category, count in (
        summary[
            "primary_category_counts"
        ].items()
    ):
        print(f"  {category}: {count}")

    print(
        "Special-status countries:",
        ", ".join(
            summary[
                "special_status_countries"
            ]
        )
        or "none",
    )

    print(
        "Pilot structure exceptions:",
        len(
            summary[
                "pilot_structure_exception_scopes"
            ]
        ),
    )


if __name__ == "__main__":
    main()
