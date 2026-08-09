from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

INCOME_TYPES = ("dividend", "interest", "royalty")

PILOT_COUNTRIES = {"AT", "CH"}

FINAL23_COUNTRIES = {
    "AD",
    "BA",
    "BB",
    "BH",
    "BW",
    "CL",
    "CM",
    "CO",
    "CY",
    "GB",
    "GH",
    "HK",
    "JP",
    "KR",
    "LU",
    "PA",
    "PL",
    "QA",
}

MF_INVENTORY = ROOT / "data/legal_consolidation/mf_inventory.json"
MIGRATION_BOUNDARY = (
    ROOT / "data/legal_consolidation/final23_migration_boundary.json"
)
STAGE4_GATE = (
    ROOT
    / "data/legal_reviews/global_cz_outbound/"
    "stage4_final_runtime_release_gate.json"
)
FINAL23_DIR = ROOT / "data/legal_rule_candidates/final23"
LEGACY_CHAIN = (
    ROOT / "data/legal_consolidation/remaining_294_instrument_chains.json"
)

OUTPUT = ROOT / "data/legal_consolidation/stage5_execution_manifest.json"


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise RuntimeError(f"Required repository file missing: {path.relative_to(ROOT)}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"Cannot parse JSON: {path.relative_to(ROOT)}: {exc}"
        ) from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_strings(item)


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_dicts(item)


def final23_country_codes_from_candidates(files: list[Path]) -> set[str]:
    observed: set[str] = set()

    country_keys = {
        "recipient_country",
        "recipient_country_code",
        "country",
        "country_code",
        "iso2",
        "partner_country",
        "partner_country_code",
        "treaty_partner",
        "treaty_partner_code",
    }

    for path in files:
        payload = load_json(path)

        for node in walk_dicts(payload):
            for key, value in node.items():
                if key in country_keys and isinstance(value, str):
                    code = value.strip().upper()
                    if code in FINAL23_COUNTRIES:
                        observed.add(code)

        stem = path.stem.upper()
        for code in FINAL23_COUNTRIES:
            if re.search(rf"(^|[^A-Z]){re.escape(code)}([^A-Z]|$)", stem):
                observed.add(code)

    return observed


def verification_status_counts(files: list[Path]) -> Counter:
    counts: Counter = Counter()

    for path in files:
        payload = load_json(path)

        for node in walk_dicts(payload):
            if "verification_status" in node:
                counts[str(node["verification_status"])] += 1

    return counts


def legacy_frozen_files() -> list[Path]:
    files: set[Path] = set()

    for base in (
        ROOT / "data/legal_consolidation",
        ROOT / "data/legal_reviews",
    ):
        if base.is_dir():
            files.update(base.rglob("*remaining*294*.json"))

    return sorted(path for path in files if path.is_file())


def operational_class(partner: dict[str, Any]) -> tuple[int, str, list[str]]:
    related = partner.get("related_instruments") or []

    source_types = {
        str(item.get("source_type"))
        for item in related
        if isinstance(item, dict)
    }

    reasons: list[str] = []

    if partner.get("protocol_listed"):
        reasons.append("protocol_listed")

    if "status_or_amendment_notice" in source_types:
        reasons.append("status_or_amendment_notice_present")

    if "correction" in source_types:
        reasons.append("correction_present")

    if partner.get("mli_listed"):
        reasons.append("mli_listed")

    if partner.get("mli_listed") and not partner.get("mli_notice_available"):
        reasons.append("mli_notice_not_available_in_inventory")

    if (
        partner.get("protocol_listed")
        or "status_or_amendment_notice" in source_types
        or "correction" in source_types
    ):
        return 1, "instrument_overlay", reasons

    if partner.get("mli_listed") and not partner.get("mli_notice_available"):
        return 2, "mli_notice_gap", reasons

    if partner.get("mli_listed"):
        return 3, "mli_workflow", reasons

    return 4, "base_treaty_workflow", reasons


def chunked(items: list[dict[str, Any]], size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def main() -> None:
    inventory = load_json(MF_INVENTORY)
    migration = load_json(MIGRATION_BOUNDARY)
    stage4_gate = load_json(STAGE4_GATE)

    partners = inventory.get("partners")
    if not isinstance(partners, list):
        raise RuntimeError("mf_inventory.json does not contain a partners list")

    partner_by_code: dict[str, dict[str, Any]] = {}

    for partner in partners:
        if not isinstance(partner, dict):
            raise RuntimeError("Unexpected non-object partner in mf_inventory.json")

        code = str(partner.get("iso2", "")).upper().strip()

        if not re.fullmatch(r"[A-Z]{2}", code):
            raise RuntimeError(f"Invalid ISO2 in MF inventory: {code!r}")

        if code in partner_by_code:
            raise RuntimeError(f"Duplicate MF inventory ISO2: {code}")

        partner_by_code[code] = partner

    universe = set(partner_by_code)

    if len(universe) != 100:
        raise RuntimeError(
            f"Expected 100 Czech treaty partners, found {len(universe)}"
        )

    if not PILOT_COUNTRIES <= universe:
        raise RuntimeError("AT/CH pilot countries missing from treaty universe")

    if not FINAL23_COUNTRIES <= universe:
        missing = sorted(FINAL23_COUNTRIES - universe)
        raise RuntimeError(f"Final23 countries missing from universe: {missing}")

    if PILOT_COUNTRIES & FINAL23_COUNTRIES:
        raise RuntimeError("AT/CH and Final23 cohorts overlap")

    final23_files = sorted(FINAL23_DIR.glob("*.json"))

    if len(final23_files) != 18:
        raise RuntimeError(
            f"Expected 18 Final23 candidate JSON files, found {len(final23_files)}"
        )

    observed_final23 = final23_country_codes_from_candidates(final23_files)

    if observed_final23 != FINAL23_COUNTRIES:
        raise RuntimeError(
            "Final23 candidate country set mismatch. "
            f"Expected={sorted(FINAL23_COUNTRIES)} "
            f"Observed={sorted(observed_final23)}"
        )

    migration_strings = set(all_strings(migration))
    migration_codes = {
        value.strip().upper()
        for value in migration_strings
        if isinstance(value, str)
        and value.strip().upper() in FINAL23_COUNTRIES
    }

    if migration_codes and migration_codes != FINAL23_COUNTRIES:
        raise RuntimeError(
            "Migration boundary contains only a partial Final23 country set: "
            f"{sorted(migration_codes)}"
        )

    final23_statuses = verification_status_counts(final23_files)

    if final23_statuses != Counter({"needs_review": 78}):
        raise RuntimeError(
            "Final23 verification-status invariant changed. "
            f"Expected 78 needs_review rules, observed {dict(final23_statuses)}"
        )

    if stage4_gate.get("stage4_complete") is not True:
        raise RuntimeError("Stage 4 release gate is no longer complete")

    if stage4_gate.get("production_legal_release_complete") is not False:
        raise RuntimeError(
            "Production legal release state changed. "
            "Do not infer Stage 5 baseline automatically."
        )

    remaining80 = universe - PILOT_COUNTRIES - FINAL23_COUNTRIES

    if len(remaining80) != 80:
        raise RuntimeError(
            f"Expected 80 countries outside AT/CH + Final23, found {len(remaining80)}"
        )

    legacy_chain_meta: dict[str, Any] = {
        "path": str(LEGACY_CHAIN.relative_to(ROOT)),
        "present": LEGACY_CHAIN.is_file(),
    }

    if LEGACY_CHAIN.is_file():
        legacy_payload = load_json(LEGACY_CHAIN)
        legacy_scopes = legacy_payload.get("scopes")

        if not isinstance(legacy_scopes, list):
            raise RuntimeError(
                "remaining_294_instrument_chains.json lacks scopes list"
            )

        if len(legacy_scopes) != 294:
            raise RuntimeError(
                "Frozen remaining_294 chain no longer contains 294 scopes"
            )

        legacy_chain_meta.update(
            {
                "sha256": sha256(LEGACY_CHAIN),
                "dataset_release": legacy_payload.get("dataset_release"),
                "scope_count": len(legacy_scopes),
            }
        )

    remaining_rows: list[dict[str, Any]] = []

    for code in sorted(remaining80):
        partner = partner_by_code[code]
        rank, workflow_class, reasons = operational_class(partner)

        remaining_rows.append(
            {
                "country": code,
                "country_name": partner.get("country"),
                "operational_priority_rank": rank,
                "workflow_class": workflow_class,
                "operational_reasons": reasons,
                "protocol_listed": bool(partner.get("protocol_listed")),
                "mli_listed": bool(partner.get("mli_listed")),
                "mli_notice_available": bool(
                    partner.get("mli_notice_available")
                ),
                "inventory_status": partner.get("inventory_status"),
                "scope_count": 3,
            }
        )

    remaining_rows.sort(
        key=lambda row: (
            row["operational_priority_rank"],
            row["country"],
        )
    )

    work_batches: list[dict[str, Any]] = []

    for number, rows in enumerate(chunked(remaining_rows, 10), start=1):
        countries = [row["country"] for row in rows]

        work_batches.append(
            {
                "batch_id": f"stage5_remaining80_batch_{number:02d}",
                "country_count": len(countries),
                "scope_count": len(countries) * 3,
                "countries": countries,
                "workflow_classes": sorted(
                    {row["workflow_class"] for row in rows}
                ),
                "purpose": (
                    "Build/reconcile new Stage 5 candidate evidence and "
                    "semantic legal chain without modifying frozen "
                    "remaining_294 review snapshots."
                ),
            }
        )

    if len(work_batches) != 8:
        raise RuntimeError(
            f"Expected eight 10-country remaining80 batches, got {len(work_batches)}"
        )

    scopes: list[dict[str, Any]] = []

    for code in sorted(universe):
        partner = partner_by_code[code]

        if code in PILOT_COUNTRIES:
            cohort = "pilot_at_ch"
            workflow_state = "existing_pilot_requires_human_release"
            legacy_policy = "not_applicable"

        elif code in FINAL23_COUNTRIES:
            cohort = "final23"
            workflow_state = "existing_final23_candidate_needs_review"
            legacy_policy = "frozen_reference_only"

        else:
            cohort = "remaining80"
            workflow_state = "new_stage5_candidate_workflow_required"
            legacy_policy = "frozen_reference_only"

        for income in INCOME_TYPES:
            scopes.append(
                {
                    "scope_id": f"CZ-{code}-{income}",
                    "source_country": "CZ",
                    "recipient_country": code,
                    "recipient_country_name": partner.get("country"),
                    "income_type": income,
                    "cohort": cohort,
                    "workflow_state": workflow_state,
                    "stage5_status": "pending",
                    "required_terminal_status": "verified_or_blocked",
                    "production_releasable": False,
                    "human_primary_review_required": True,
                    "independent_approval_required_if_verified": True,
                    "legacy_remaining_294_policy": legacy_policy,
                }
            )

    if len(scopes) != 300:
        raise RuntimeError(f"Expected 300 scopes, generated {len(scopes)}")

    frozen_files = legacy_frozen_files()

    frozen_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in frozen_files
    }

    manifest = {
        "schema_version": 1,
        "dataset_release": "stage5-execution-control-plane-2026-08-09.1",
        "purpose": (
            "Deterministic Stage 5 execution and migration control plane. "
            "This file contains no legal approval and no production rule."
        ),
        "legal_safety": {
            "official_source_is_authority": True,
            "extraction_is_not_verification": True,
            "provenance_is_not_approval": True,
            "candidate_is_not_production_rule": True,
            "needs_review_cannot_produce_final": True,
            "legacy_remaining_294_is_frozen": True,
            "final23_candidate_directory_is_not_production_rules": True,
            "human_review_metadata_must_not_be_fabricated": True,
        },
        "stage4_boundary": {
            "path": str(STAGE4_GATE.relative_to(ROOT)),
            "sha256": sha256(STAGE4_GATE),
            "stage4_complete": True,
            "production_legal_release_complete": False,
        },
        "migration_boundary": {
            "path": str(MIGRATION_BOUNDARY.relative_to(ROOT)),
            "sha256": sha256(MIGRATION_BOUNDARY),
            "final23_expected_country_count": 18,
            "final23_expected_scope_count": 54,
            "final23_candidate_rule_count": 78,
            "final23_verification_status_counts": dict(final23_statuses),
        },
        "universe": {
            "country_count": 100,
            "scope_count": 300,
            "income_types": list(INCOME_TYPES),
            "terminal_verified_count": 0,
            "terminal_blocked_count": 0,
            "pending_stage5_count": 300,
        },
        "cohorts": {
            "pilot_at_ch": {
                "countries": sorted(PILOT_COUNTRIES),
                "country_count": 2,
                "scope_count": 6,
            },
            "final23": {
                "countries": sorted(FINAL23_COUNTRIES),
                "country_count": 18,
                "scope_count": 54,
                "candidate_rule_count": 78,
                "verification_status": "needs_review",
            },
            "remaining80": {
                "countries": sorted(remaining80),
                "country_count": 80,
                "scope_count": 240,
            },
        },
        "legacy_snapshot": legacy_chain_meta,
        "frozen_remaining_294_hashes": frozen_hashes,
        "remaining80_operational_inventory": remaining_rows,
        "remaining80_work_batches": work_batches,
        "stage5_milestones": [
            {
                "percent": 5,
                "definition": (
                    "Execution control plane, complete 300-scope ledger, "
                    "migration boundaries and frozen-hash protection."
                ),
            },
            {
                "percent": 20,
                "definition": (
                    "Remaining80 migrated into the new candidate evidence "
                    "workflow using official-source identities."
                ),
            },
            {
                "percent": 40,
                "definition": (
                    "Articles 10-12 and material conditions semantically "
                    "mapped for remaining80."
                ),
            },
            {
                "percent": 55,
                "definition": (
                    "Protocol/amendment, MLI, effective-date, status and "
                    "language-authority layers reconciled."
                ),
            },
            {
                "percent": 70,
                "definition": (
                    "Treaty chains reconciled with Czech domestic/EU layers "
                    "and exact provenance."
                ),
            },
            {
                "percent": 85,
                "definition": (
                    "Complete 300-scope candidate coverage with end-to-end "
                    "fail-closed and no-gap tests."
                ),
            },
            {
                "percent": 98,
                "definition": (
                    "Human primary review and independent approval completed, "
                    "or precise legal blockers recorded."
                ),
            },
            {
                "percent": 100,
                "definition": (
                    "Final Stage 5 completeness/release audit, documentation "
                    "and full regression suite complete."
                ),
            },
        ],
        "scopes": scopes,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("Stage 5 execution manifest generated successfully.")
    print("Countries:", manifest["universe"]["country_count"])
    print("Scopes:", manifest["universe"]["scope_count"])
    print("AT/CH scopes:", manifest["cohorts"]["pilot_at_ch"]["scope_count"])
    print("Final23 scopes:", manifest["cohorts"]["final23"]["scope_count"])
    print(
        "Final23 candidate rules:",
        manifest["cohorts"]["final23"]["candidate_rule_count"],
    )
    print(
        "Final23 verification statuses:",
        manifest["migration_boundary"][
            "final23_verification_status_counts"
        ],
    )
    print(
        "Remaining80 scopes:",
        manifest["cohorts"]["remaining80"]["scope_count"],
    )
    print("Remaining80 batches:", len(work_batches))
    print("Frozen remaining_294 files:", len(frozen_hashes))
    print("Production releasable scopes: 0")
    print("Stage 5 terminal status: 0 verified / 0 blocked / 300 pending")


if __name__ == "__main__":
    main()
