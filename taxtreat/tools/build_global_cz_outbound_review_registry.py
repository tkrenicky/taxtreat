from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"

DOMESTIC_PATH = (
    DATA_DIR
    / "legal_consolidation"
    / "cz_domestic_eu_candidates.json"
)

CHAINS_PATH = (
    DATA_DIR
    / "legal_consolidation"
    / "remaining_294_instrument_chains.json"
)

PROTOCOL_PATH = (
    DATA_DIR
    / "legal_consolidation"
    / "protocol_effect_candidates.json"
)

MLI_PATH = (
    DATA_DIR
    / "legal_consolidation"
    / "mli_wht_effects.json"
)

BATCH_01_PATH = (
    DATA_DIR
    / "legal_reviews"
    / "batches"
    / "batch_01_review_matrix.json"
)

OUTPUT_DIR = (
    DATA_DIR
    / "legal_reviews"
    / "global_cz_outbound"
)

PACKS_DIR = OUTPUT_DIR / "packs"

INDEX_PATH = OUTPUT_DIR / "global_review_index.json"
QUEUE_PATH = OUTPUT_DIR / "global_review_queue.json"
COVERAGE_PATH = OUTPUT_DIR / "global_review_coverage.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def scope_key(
    recipient_country: str,
    income_type: str,
) -> tuple[str, str]:
    return recipient_country, income_type


def packet_id(
    recipient_country: str,
    income_type: str,
) -> str:
    income_codes = {
        "dividend": "DIV",
        "interest": "INT",
        "royalty": "ROY",
    }

    return (
        f"CZ-{recipient_country}-"
        f"{income_codes[income_type]}-LEGAL-REVIEW"
    )


def index_by_scope(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for row in rows:
        key = scope_key(
            row["recipient_country"],
            row["income_type"],
        )

        if key in result:
            raise ValueError(
                f"Duplicate scope: {key[0]}/{key[1]}"
            )

        result[key] = row

    return result


def mli_index(
    effects: list[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    result: dict[
        tuple[str, str],
        list[dict[str, Any]],
    ] = {}

    for effect in effects:
        country = effect["recipient_country"]

        for income_type in effect.get(
            "applies_to_income_types",
            [],
        ):
            key = scope_key(country, income_type)
            result.setdefault(key, []).append(effect)

    return result


def build_pack(
    domestic_scope: dict[str, Any],
    *,
    chain: dict[str, Any] | None,
    protocol: dict[str, Any] | None,
    mli_effects: list[dict[str, Any]],
    batch_row: dict[str, Any] | None,
) -> dict[str, Any]:
    country = domestic_scope["recipient_country"]
    income_type = domestic_scope["income_type"]

    legal_layers = {
        "domestic_and_eu": domestic_scope,
        "instrument_chain": chain,
        "protocol_effect": protocol,
        "mli_effects": mli_effects,
        "priority_review_row": batch_row,
    }

    blockers: list[str] = []

    blockers.extend(
        domestic_scope.get(
            "consolidation_blockers",
            [],
        )
    )

    if chain is None and batch_row is None:
        blockers.append(
            "missing_instrument_chain_or_priority_review_row"
        )

    if chain is not None:
        blockers.extend(
            chain.get("hard_blockers", [])
        )

        if not chain.get(
            "candidate_chain_complete",
            False,
        ):
            blockers.append(
                "candidate_instrument_chain_incomplete"
            )

    treaty_source_ids: list[str] = []

    if batch_row:
        source_id = (
            batch_row.get("base_treaty", {})
            .get("source_id")
        )

        if source_id:
            treaty_source_ids.append(source_id)

    if chain:
        base_treaty = chain.get(
            "base_treaty",
            {},
        )

        for field in (
            "source_id",
            "source_page_id",
            "publication_source_id",
        ):
            value = base_treaty.get(field)

            if value:
                treaty_source_ids.append(value)

    supporting_source_ids = sorted(
        {
            source_id
            for source_id in (
                treaty_source_ids
                + [
                    (
                        domestic_scope.get(
                            "domestic_rate_candidate"
                        )
                        or {}
                    ).get("source_id"),
                    (
                        domestic_scope.get(
                            "relief_candidate"
                        )
                        or {}
                    ).get("directive_source_id"),
                ]
                + (
                    protocol.get(
                        "protocol_source_ids",
                        [],
                    )
                    if protocol
                    else []
                )
                + [
                    effect.get("source_page_id")
                    for effect in mli_effects
                ]
            )
            if source_id
        }
    )

    candidate_readiness = (
        "review_ready"
        if (
            not blockers
            and supporting_source_ids
        )
        else "blocked"
    )

    pack_body = {
        "packet_id": packet_id(
            country,
            income_type,
        ),
        "source_country": "CZ",
        "recipient_country": country,
        "recipient_country_name": domestic_scope[
            "recipient_country_name"
        ],
        "income_type": income_type,
        "candidate_readiness": candidate_readiness,
        "legal_layers": legal_layers,
        "blockers": sorted(set(blockers)),
        "supporting_source_ids": (
            supporting_source_ids
        ),
    }

    return {
        "schema_version": 1,
        "review_pack_sha256": canonical_sha256(
            pack_body
        ),
        **pack_body,
        "review": {
            "reviewer_id": None,
            "reviewed_at": None,
            "question_responses": [],
            "confirmations": {
                "treaty_rules_confirmed": None,
                "domestic_law_confirmed": None,
                "eu_relief_confirmed": None,
                "protocol_effects_confirmed": None,
                "mli_effects_confirmed": None,
                "effective_dates_confirmed": None,
                "anti_abuse_review_completed": None,
            },
            "proposed_rule_snapshot": None,
            "review_outcome": None,
        },
        "status": "awaiting_primary_review",
        "approval_eligible": False,
        "promotable_to_active_rules": False,
    }


def build_global_registry() -> dict[str, Any]:
    domestic_payload = read_json(DOMESTIC_PATH)
    chains_payload = read_json(CHAINS_PATH)
    protocol_payload = read_json(PROTOCOL_PATH)
    mli_payload = read_json(MLI_PATH)
    batch_payload = read_json(BATCH_01_PATH)

    domestic_rows = domestic_payload["scopes"]

    chain_rows = index_by_scope(
        chains_payload["scopes"]
    )

    protocol_rows = index_by_scope(
        protocol_payload["scopes"]
    )

    batch_rows = index_by_scope(
        batch_payload["rows"]
    )

    indexed_mli = mli_index(
        mli_payload["effects"]
    )

    packs = []

    for domestic_scope in domestic_rows:
        key = scope_key(
            domestic_scope["recipient_country"],
            domestic_scope["income_type"],
        )

        packs.append(
            build_pack(
                domestic_scope,
                chain=chain_rows.get(key),
                protocol=protocol_rows.get(key),
                mli_effects=indexed_mli.get(
                    key,
                    [],
                ),
                batch_row=batch_rows.get(key),
            )
        )

    packs.sort(
        key=lambda pack: (
            pack["recipient_country"],
            pack["income_type"],
        )
    )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-cz-outbound-review-registry-"
            "2026-08-06.1"
        ),
        "policy": {
            "scope_target": 300,
            "human_primary_review_required": True,
            "independent_approval_required": True,
            "automatic_legal_confirmation_prohibited": True,
            "fail_closed": True,
        },
        "packs": packs,
    }


def write_outputs(
    registry: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    PACKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    packs = registry["packs"]

    for pack in packs:
        path = (
            PACKS_DIR
            / f"{pack['packet_id'].lower()}.json"
        )

        path.write_text(
            json.dumps(
                pack,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    status_counts = Counter(
        pack["status"]
        for pack in packs
    )

    readiness_counts = Counter(
        pack["candidate_readiness"]
        for pack in packs
    )

    country_count = len(
        {
            pack["recipient_country"]
            for pack in packs
        }
    )

    income_counts = Counter(
        pack["income_type"]
        for pack in packs
    )

    index_payload = {
        "schema_version": 1,
        "dataset_release": registry[
            "dataset_release"
        ],
        "scope_count": len(packs),
        "country_count": country_count,
        "income_type_counts": dict(
            sorted(income_counts.items())
        ),
        "pack_files": [
            {
                "packet_id": pack["packet_id"],
                "recipient_country": pack[
                    "recipient_country"
                ],
                "income_type": pack["income_type"],
                "candidate_readiness": pack[
                    "candidate_readiness"
                ],
                "status": pack["status"],
                "review_pack_sha256": pack[
                    "review_pack_sha256"
                ],
                "path": (
                    "packs/"
                    f"{pack['packet_id'].lower()}.json"
                ),
            }
            for pack in packs
        ],
    }

    queue_payload = {
        "schema_version": 1,
        "dataset_release": registry[
            "dataset_release"
        ],
        "summary": {
            "total_scopes": len(packs),
            "awaiting_primary_review": (
                status_counts[
                    "awaiting_primary_review"
                ]
            ),
            "awaiting_independent_approval": 0,
            "promotable_scopes": 0,
        },
        "queue": [
            {
                "packet_id": pack["packet_id"],
                "recipient_country": pack[
                    "recipient_country"
                ],
                "income_type": pack["income_type"],
                "candidate_readiness": pack[
                    "candidate_readiness"
                ],
                "blocker_count": len(
                    pack["blockers"]
                ),
                "status": pack["status"],
            }
            for pack in packs
        ],
    }

    coverage_payload = {
        "schema_version": 1,
        "dataset_release": registry[
            "dataset_release"
        ],
        "target_scopes": 300,
        "actual_scopes": len(packs),
        "target_countries": 100,
        "actual_countries": country_count,
        "income_type_counts": dict(
            sorted(income_counts.items())
        ),
        "candidate_readiness_counts": dict(
            sorted(readiness_counts.items())
        ),
        "status_counts": dict(
            sorted(status_counts.items())
        ),
        "scope_coverage_percent": round(
            len(packs) / 300 * 100,
            2,
        ),
        "country_coverage_percent": round(
            country_count / 100 * 100,
            2,
        ),
        "all_scopes_fail_closed": all(
            pack["status"]
            == "awaiting_primary_review"
            and pack["approval_eligible"] is False
            and pack[
                "promotable_to_active_rules"
            ]
            is False
            for pack in packs
        ),
    }

    INDEX_PATH.write_text(
        json.dumps(
            index_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    QUEUE_PATH.write_text(
        json.dumps(
            queue_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    COVERAGE_PATH.write_text(
        json.dumps(
            coverage_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    registry = build_global_registry()
    write_outputs(registry)

    coverage = read_json(COVERAGE_PATH)

    if coverage["actual_scopes"] != 300:
        raise RuntimeError(
            "Global review registry must contain "
            "exactly 300 scopes."
        )

    if coverage["actual_countries"] != 100:
        raise RuntimeError(
            "Global review registry must contain "
            "exactly 100 countries."
        )

    if not coverage["all_scopes_fail_closed"]:
        raise RuntimeError(
            "Every global review scope must remain "
            "fail-closed."
        )

    print("Global CZ outbound review registry created.")
    print("Scopes:", coverage["actual_scopes"])
    print("Countries:", coverage["actual_countries"])
    print(
        "Income types:",
        coverage["income_type_counts"],
    )
    print(
        "Candidate readiness:",
        coverage[
            "candidate_readiness_counts"
        ],
    )
    print(
        "All scopes fail closed:",
        coverage["all_scopes_fail_closed"],
    )


if __name__ == "__main__":
    main()
