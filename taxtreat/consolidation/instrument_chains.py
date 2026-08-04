from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONSOLIDATION_DIR = ROOT / "data" / "legal_consolidation"
DEFAULT_INVENTORY = CONSOLIDATION_DIR / "mf_inventory.json"
DEFAULT_BASE_CANDIDATES = (
    CONSOLIDATION_DIR / "remaining_294_base_candidates.json"
)
DEFAULT_PROTOCOL_EFFECTS = (
    CONSOLIDATION_DIR / "protocol_effect_candidates.json"
)
DEFAULT_MLI_EFFECTS = CONSOLIDATION_DIR / "mli_wht_effects.json"
DEFAULT_DOMESTIC_EU = (
    CONSOLIDATION_DIR / "cz_domestic_eu_candidates.json"
)
DEFAULT_OUTPUT = (
    CONSOLIDATION_DIR / "remaining_294_instrument_chains.json"
)

PILOT_CODES = {"AT", "CH"}
SUPPORTED_INCOME_TYPES = {"dividend", "interest", "royalty"}


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _scope_index(
    payload: dict[str, Any],
    *,
    expected_count: int,
    label: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in payload.get("scopes", []):
        key = (row["recipient_country"], row["income_type"])
        if key in index:
            raise ValueError(f"Duplicate {label} scope: {key!r}.")
        index[key] = row
    if len(index) != expected_count:
        raise ValueError(
            f"Expected {expected_count} {label} scopes, found {len(index)}."
        )
    return index


def _candidate_sha256(scope: dict[str, Any]) -> str:
    canonical = json.dumps(
        scope,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _mli_status(
    inventory: dict[str, Any],
    effect: dict[str, Any] | None,
) -> str:
    if not inventory["mli_listed"]:
        return "not_listed"
    if effect is not None:
        return "wht_effect_candidate_available"
    if inventory["mli_notice_available"]:
        return "official_notice_requires_wht_effect_extraction"
    return "matching_and_effective_date_required"


def _build_scope(
    *,
    inventory: dict[str, Any],
    base: dict[str, Any],
    protocol: dict[str, Any] | None,
    mli_effect: dict[str, Any] | None,
    domestic: dict[str, Any],
    dataset_releases: dict[str, str],
) -> dict[str, Any]:
    country = base["recipient_country"]
    income_type = base["income_type"]
    protocol_required = inventory["protocol_listed"]
    mli_status = _mli_status(inventory, mli_effect)
    relief = domestic["relief_candidate"]

    hard_blockers: list[str] = []
    if not base["rate_candidates"]:
        hard_blockers.append("base_treaty_rate_manual_consolidation")
    if protocol_required and protocol is None:
        hard_blockers.append("protocol_effect_candidate_missing")
    if mli_status == "official_notice_requires_wht_effect_extraction":
        hard_blockers.append("mli_wht_effect_extraction")
    elif mli_status == "matching_and_effective_date_required":
        hard_blockers.append("mli_matching_and_effective_date")
    if country in {"BY", "RU"}:
        hard_blockers.append("post_protocol_status_instrument_consolidation")

    review_tasks = {
        "base_treaty_candidate_review",
        "domestic_rate_candidate_review",
        "independent_legal_review",
    }
    if base["risk_flags"]:
        review_tasks.add("semantic_rate_review")
    if protocol is not None:
        review_tasks.add("protocol_effect_candidate_review")
    if mli_effect is not None:
        review_tasks.add("mli_wht_effect_candidate_review")
    if relief is not None:
        review_tasks.update(
            {
                "anti_abuse_determination",
                "recipient_qualification_fact_review",
                "relief_candidate_review",
            }
        )

    chain_complete = not hard_blockers
    scope = {
        "source_country": "CZ",
        "recipient_country": country,
        "recipient_country_name": base["recipient_country_name"],
        "income_type": income_type,
        "instrument_inventory": {
            "entry_into_force": inventory["entry_into_force"],
            "base_source_ids": sorted(
                source["source_id"] for source in inventory["base_instruments"]
            ),
            "related_source_ids": sorted(
                source["source_id"]
                for source in inventory["related_instruments"]
            ),
            "protocol_listed": protocol_required,
            "mli_listed": inventory["mli_listed"],
        },
        "base_treaty": {
            "source_id": base["base_treaty_source_id"],
            "article_number": base["article_number"],
            "article_text_sha256": base["article_text_sha256"],
            "candidate_rates": sorted(
                {candidate["rate"] for candidate in base["rate_candidates"]}
            ),
            "candidate_status": base["candidate_status"],
            "risk_flags": base["risk_flags"],
        },
        "protocol": {
            "required": protocol_required,
            "candidate_status": (
                protocol["candidate_status"]
                if protocol is not None
                else "not_listed"
                if not protocol_required
                else "missing"
            ),
            "effect_kind": (
                protocol.get("effect_kind") if protocol is not None else None
            ),
            "candidate_effective_from": (
                protocol.get("protocol_candidate_effective_from")
                if protocol is not None
                else None
            ),
            "candidate_rates": sorted(
                {
                    candidate["rate"]
                    for candidate in (
                        protocol.get("protocol_rate_candidates", [])
                        if protocol is not None
                        else []
                    )
                }
            ),
            "source_ids": (
                protocol["protocol_source_ids"] if protocol is not None else []
            ),
        },
        "mli": {
            "status": mli_status,
            "effect_id": (
                mli_effect.get("effect_id") if mli_effect is not None else None
            ),
            "effective_from": (
                mli_effect.get("effective_from")
                if mli_effect is not None
                else None
            ),
            "source_page_id": (
                mli_effect.get("source_page_id")
                if mli_effect is not None
                else None
            ),
            "source_excerpt_sha256": (
                mli_effect.get("source_excerpt_sha256")
                if mli_effect is not None
                else None
            ),
        },
        "czech_domestic_law": {
            "candidate_status": domestic["candidate_status"],
            "effective_from": domestic["domestic_rate_candidate"][
                "effective_from"
            ],
            "standard_rate": domestic["domestic_rate_candidate"][
                "standard_rate"
            ],
            "protective_rate": domestic["domestic_rate_candidate"][
                "protective_rate"
            ],
            "source_id": domestic["domestic_rate_candidate"]["source_id"],
        },
        "section_19_relief": {
            "jurisdiction_eligible": relief is not None,
            "candidate_status": domestic["relief_candidate_status"],
            "candidate_rate": relief.get("rate") if relief is not None else None,
            "regime": relief.get("regime") if relief is not None else None,
            "legal_reference": (
                relief.get("legal_reference") if relief is not None else None
            ),
        },
        "candidate_dataset_releases": dataset_releases,
        "hard_blockers": sorted(hard_blockers),
        "legal_review_tasks": sorted(review_tasks),
        "candidate_chain_complete": chain_complete,
        "chain_status": (
            "candidate_chain_assembled"
            if chain_complete
            else "candidate_chain_blocked"
        ),
        "verification_status": "needs_review",
        "review_ready": False,
    }
    scope["candidate_sha256"] = _candidate_sha256(scope)
    return scope


def build_instrument_chains(
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY,
    base_candidates_path: str | Path = DEFAULT_BASE_CANDIDATES,
    protocol_effects_path: str | Path = DEFAULT_PROTOCOL_EFFECTS,
    mli_effects_path: str | Path = DEFAULT_MLI_EFFECTS,
    domestic_eu_path: str | Path = DEFAULT_DOMESTIC_EU,
) -> dict[str, Any]:
    inventory_payload = _read_json(inventory_path)
    base_payload = _read_json(base_candidates_path)
    protocol_payload = _read_json(protocol_effects_path)
    mli_payload = _read_json(mli_effects_path)
    domestic_payload = _read_json(domestic_eu_path)

    inventory = {
        row["iso2"]: row for row in inventory_payload.get("partners", [])
    }
    if len(inventory) != 100:
        raise ValueError("Instrument inventory must cover 100 partners.")
    base = _scope_index(
        base_payload,
        expected_count=294,
        label="base-treaty candidate",
    )
    protocols = _scope_index(
        protocol_payload,
        expected_count=33,
        label="protocol-effect candidate",
    )
    domestic = _scope_index(
        domestic_payload,
        expected_count=300,
        label="domestic/EU candidate",
    )
    mli_effects = {
        row["recipient_country"]: row
        for row in mli_payload.get("effects", [])
    }
    if len(mli_effects) != 62:
        raise ValueError("MLI WHT effect registry must cover 62 partners.")

    expected_keys = {
        (country, income_type)
        for country in inventory
        if country not in PILOT_CODES
        for income_type in SUPPORTED_INCOME_TYPES
    }
    if set(base) != expected_keys:
        raise ValueError("Base candidates do not match the non-pilot scope.")
    if not set(protocols).issubset(expected_keys):
        raise ValueError("Protocol candidates contain a scope outside the baseline.")
    if not expected_keys.issubset(domestic):
        raise ValueError("Domestic/EU candidates do not cover the baseline.")

    dataset_releases = {
        "base_treaty": base_payload["dataset_release"],
        "protocol": protocol_payload["dataset_release"],
        "mli": mli_payload["dataset_release"],
        "domestic_eu": domestic_payload["dataset_release"],
    }
    scopes = []
    for country, income_type in sorted(expected_keys):
        scopes.append(
            _build_scope(
                inventory=inventory[country],
                base=base[(country, income_type)],
                protocol=protocols.get((country, income_type)),
                mli_effect=mli_effects.get(country),
                domestic=domestic[(country, income_type)],
                dataset_releases=dataset_releases,
            )
        )

    blocker_counts = Counter(
        blocker for scope in scopes for blocker in scope["hard_blockers"]
    )
    blocker_queue = [
        {
            "blocker": blocker,
            "affected_scopes": count,
            "affected_partners": sorted(
                {
                    scope["recipient_country"]
                    for scope in scopes
                    if blocker in scope["hard_blockers"]
                }
            ),
        }
        for blocker, count in sorted(blocker_counts.items())
    ]

    assembled = sum(scope["candidate_chain_complete"] for scope in scopes)
    blocked = len(scopes) - assembled
    if (assembled, blocked) != (260, 34):
        raise ValueError(
            "Expected 260 assembled and 34 blocked candidate chains; "
            f"found {assembled} and {blocked}."
        )

    return {
        "schema_version": 1,
        "dataset_release": "remaining-294-instrument-chains-2026-08-04.1",
        "source_cutoffs": {
            "mf_instrument_inventory": inventory_payload["source_page"][
                "legal_data_cutoff"
            ],
            "base_treaty_candidates": base_payload["legal_data_cutoff"],
            "protocol_effect_candidates": protocol_payload[
                "legal_data_cutoff"
            ],
            "mli_wht_effect_candidates": mli_payload["legal_data_cutoff"],
            "czech_domestic_eu_candidates": domestic_payload[
                "legal_data_cutoff"
            ],
        },
        "scope_exclusions": {
            "AT": "covered by the AT/CH pilot",
            "CH": "covered by the AT/CH pilot",
        },
        "summary": {
            "total_scopes": len(scopes),
            "candidate_chain_assembled_scopes": assembled,
            "candidate_chain_blocked_scopes": blocked,
            "blocked_partners": len(
                {
                    scope["recipient_country"]
                    for scope in scopes
                    if not scope["candidate_chain_complete"]
                }
            ),
            "review_ready_scopes": 0,
            "verified_scopes": 0,
        },
        "blocker_queue": blocker_queue,
        "scopes": scopes,
    }


def write_instrument_chains(
    payload: dict[str, Any],
    path: str | Path = DEFAULT_OUTPUT,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
