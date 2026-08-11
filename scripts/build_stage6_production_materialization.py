from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

BASE = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

QUEUE = BASE / "cz_country_qa_queue.json"
APPROVAL = BASE / "stage6_production_approval.json"
CANONICAL_GATE = (
    BASE / "production_source_release_gate_v2.json"
)

OUTPUT = (
    BASE / "stage6_production_materialization_readiness.json"
)

SUMMARY = (
    BASE
    / "stage6_production_materialization_readiness_summary.json"
)

INCOMES = (
    "dividend",
    "interest",
    "royalty",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def canonical_hash(payload: dict[str, Any]) -> str:
    clone = dict(payload)
    clone.pop("package_sha256", None)

    encoded = json.dumps(
        clone,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


queue = read_json(QUEUE)
approval = read_json(APPROVAL)
gate = read_json(CANONICAL_GATE)

packages = queue["packages"]

if len(packages) != 101:
    raise RuntimeError(
        f"Expected 101 country packages; "
        f"found {len(packages)}."
    )

approval_by_pair = {
    row["treaty_pair_id"]: row
    for row in approval["records"]
}

gate_by_pair = {
    row["treaty_pair_id"]: row
    for row in gate["treaty_partners"]
}

if len(approval_by_pair) != 101:
    raise RuntimeError(
        "Production approval must cover 101 packages."
    )

if len(gate_by_pair) != 101:
    raise RuntimeError(
        "Canonical gate must cover 101 packages."
    )

records = []

for package in sorted(
    packages,
    key=lambda row: row["treaty_pair_id"],
):
    pair_id = package["treaty_pair_id"]
    country = package["partner_country"]
    package_hash = package["package_sha256"]

    blockers: list[str] = []
    warnings: list[str] = []

    approval_row = approval_by_pair.get(pair_id)
    gate_row = gate_by_pair.get(pair_id)

    if approval_row is None:
        blockers.append(
            "production_approval_record_missing"
        )
    elif (
        approval_row["package_sha256"]
        != package_hash
    ):
        blockers.append(
            "production_approval_hash_mismatch"
        )

    if gate_row is None:
        blockers.append(
            "canonical_gate_record_missing"
        )
    else:
        if (
            gate_row["package_sha256"]
            != package_hash
        ):
            blockers.append(
                "canonical_gate_hash_mismatch"
            )

        if (
            gate_row["production_approval_status"]
            != "production_approved"
        ):
            blockers.append(
                "canonical_gate_not_production_approved"
            )

    scopes = package.get("income_scopes")

    if not isinstance(scopes, list):
        blockers.append(
            "income_scopes_missing"
        )
        scopes = []

    scope_by_income = {
        row.get("income_type"): row
        for row in scopes
        if isinstance(row, dict)
    }

    if set(scope_by_income) != set(INCOMES):
        blockers.append(
            "three_income_scope_universe_incomplete"
        )

    scope_results = []

    for income in INCOMES:
        scope = scope_by_income.get(income)

        scope_blockers: list[str] = []
        scope_warnings: list[str] = []

        if scope is None:
            scope_blockers.append(
                "income_scope_missing"
            )

            scope_results.append(
                {
                    "income_type": income,
                    "materializable": False,
                    "blockers": scope_blockers,
                    "warnings": scope_warnings,
                }
            )
            continue

        article_number = scope.get(
            "article_number"
        )

        candidate_rates = scope.get(
            "candidate_rates"
        )

        material_conditions = scope.get(
            "material_conditions"
        )

        candidate_excerpt = scope.get(
            "candidate_excerpt"
        )

        article_hash = scope.get(
            "article_text_sha256"
        )

        if article_number in (None, ""):
            scope_blockers.append(
                "treaty_article_number_missing"
            )

        if not isinstance(
            candidate_rates,
            list,
        ):
            scope_blockers.append(
                "candidate_rates_missing"
            )
            candidate_rates = []

        if not isinstance(
            material_conditions,
            list,
        ):
            scope_blockers.append(
                "material_conditions_missing"
            )
            material_conditions = []

        if (
            not isinstance(
                candidate_excerpt,
                str,
            )
            or not candidate_excerpt.strip()
        ):
            scope_blockers.append(
                "candidate_excerpt_missing"
            )

        if (
            not isinstance(
                article_hash,
                str,
            )
            or len(article_hash) != 64
        ):
            scope_blockers.append(
                "article_text_hash_missing"
            )

        material_rate_set = {
            row.get("rate")
            for row in material_conditions
            if isinstance(row, dict)
        }

        candidate_rate_set = set(
            candidate_rates
        )

        if (
            candidate_rate_set
            != material_rate_set
        ):
            scope_blockers.append(
                "rate_condition_mapping_incomplete"
            )

        for node in material_conditions:
            if not isinstance(node, dict):
                scope_blockers.append(
                    "invalid_rate_condition_node"
                )
                continue

            rate = node.get("rate")

            if not isinstance(
                rate,
                (int, float),
            ):
                scope_blockers.append(
                    "non_numeric_candidate_rate"
                )

            conditions = node.get(
                "conditions"
            )

            if not isinstance(
                conditions,
                list,
            ):
                scope_blockers.append(
                    "conditions_not_list"
                )
                continue

            for condition in conditions:
                if not isinstance(
                    condition,
                    dict,
                ):
                    scope_blockers.append(
                        "invalid_condition_node"
                    )
                    continue

                if not (
                    condition.get(
                        "condition_type"
                    )
                    or condition.get("fact")
                ):
                    scope_blockers.append(
                        "condition_fact_missing"
                    )

                if not condition.get(
                    "operator"
                ):
                    scope_blockers.append(
                        "condition_operator_missing"
                    )

        eu = (
            package.get(
                "eu_directive_interaction",
                {},
            )
            or {}
        ).get(income)

        if eu is None:
            scope_warnings.append(
                "eu_interaction_not_materialized"
            )

        scope_results.append(
            {
                "income_type": income,
                "article_number":
                    article_number,
                "candidate_rates":
                    candidate_rates,
                "materializable":
                    not scope_blockers,
                "blockers":
                    sorted(
                        set(scope_blockers)
                    ),
                "warnings":
                    sorted(
                        set(scope_warnings)
                    ),
            }
        )

        blockers.extend(
            f"{income}:{value}"
            for value in scope_blockers
        )

        warnings.extend(
            f"{income}:{value}"
            for value in scope_warnings
        )

    domestic = package.get(
        "czech_domestic_wht"
    )

    if not isinstance(domestic, dict):
        blockers.append(
            "czech_domestic_wht_missing"
        )
    else:
        if domestic.get(
            "standard_rate"
        ) is None:
            blockers.append(
                "domestic_standard_rate_missing"
            )

        if domestic.get(
            "effective_from"
        ) in (None, ""):
            blockers.append(
                "domestic_effective_date_missing"
            )

        if domestic.get(
            "source_id"
        ) in (None, ""):
            blockers.append(
                "domestic_source_id_missing"
            )

    base_treaty = package.get(
        "base_treaty"
    )

    if not isinstance(
        base_treaty,
        dict,
    ):
        blockers.append(
            "base_treaty_missing"
        )
    else:
        if not base_treaty.get(
            "source_id"
        ):
            blockers.append(
                "base_treaty_source_id_missing"
            )

        if not base_treaty.get(
            "official_urls"
        ):
            blockers.append(
                "base_treaty_official_url_missing"
            )

    chain = package.get(
        "current_instrument_chain"
    )

    if not isinstance(chain, dict):
        blockers.append(
            "instrument_chain_missing"
        )

    effective = package.get(
        "effective_date_evidence"
    )

    if not isinstance(
        effective,
        dict,
    ):
        blockers.append(
            "effective_date_evidence_missing"
        )

    language = package.get(
        "language_and_prevailing_text"
    )

    if not isinstance(
        language,
        dict,
    ):
        blockers.append(
            "language_authority_missing"
        )

    ppt = package.get(
        "ppt_treatment"
    )

    if not isinstance(ppt, dict):
        blockers.append(
            "ppt_treatment_missing"
        )

    records.append(
        {
            "treaty_pair_id":
                pair_id,
            "partner_country":
                country,
            "package_sha256":
                package_hash,
            "scope_count":
                len(scopes),
            "materialization_ready":
                not blockers,
            "blockers":
                sorted(
                    set(blockers)
                ),
            "warnings":
                sorted(
                    set(warnings)
                ),
            "income_scopes":
                scope_results,
        }
    )

ready = [
    row
    for row in records
    if row["materialization_ready"]
]

blocked = [
    row
    for row in records
    if not row["materialization_ready"]
]

payload = {
    "schema_version": 1,
    "dataset_release":
        "stage6-production-materialization-readiness-2026-08-11.1",

    "semantics": {
        "this_is_rule_promotion":
            False,
        "this_is_source_release":
            False,
        "this_opens_runtime":
            False,
        "production_approval_required":
            True,
        "exact_package_hash_binding_required":
            True,
        "candidate_evidence_is_not_reclassified_as_verified":
            True,
    },

    "counts": {
        "packages": 101,
        "scopes": 303,
        "production_approved_packages": 101,
        "materialization_ready_packages":
            len(ready),
        "materialization_blocked_packages":
            len(blocked),
        "rule_promoted_packages": 0,
        "released_packages": 0,
    },

    "records":
        records,
}

summary = {
    "dataset_release":
        payload["dataset_release"],
    "packages":
        101,
    "scopes":
        303,
    "materialization_ready_packages":
        len(ready),
    "materialization_blocked_packages":
        len(blocked),
    "blocked_pairs": [
        row["treaty_pair_id"]
        for row in blocked
    ],
    "rule_promoted_packages":
        0,
    "released_packages":
        0,
}

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

SUMMARY.write_text(
    json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print("Stage 6E1 materialization readiness audit created.")
print(
    "Packages:",
    len(records),
)
print(
    "Scopes:",
    sum(
        row["scope_count"]
        for row in records
    ),
)
print(
    "Materialization ready:",
    len(ready),
)
print(
    "Materialization blocked:",
    len(blocked),
)

if blocked:
    print()
    print("BLOCKED PAIRS:")
    for row in blocked:
        print(
            row["treaty_pair_id"],
            "=>",
            "; ".join(
                row["blockers"]
            ),
        )
