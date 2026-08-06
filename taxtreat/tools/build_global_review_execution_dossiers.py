from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

GLOBAL_DIR = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

BATCHES_PATH = (
    GLOBAL_DIR
    / "global_review_batches.json"
)

WORKSTREAMS_PATH = (
    GLOBAL_DIR
    / "global_review_workstreams.json"
)

OUTPUT_DIR = (
    GLOBAL_DIR
    / "execution_dossiers"
)

INDEX_PATH = (
    GLOBAL_DIR
    / "global_review_execution_dossiers.json"
)

SUMMARY_PATH = (
    GLOBAL_DIR
    / "global_review_execution_dossiers_summary.json"
)


REVIEW_REQUIREMENTS = {
    "treaty_status_instrument_review": [
        "Confirm current treaty status",
        "Identify suspension or termination instrument",
        "Determine affected treaty provisions",
        "Confirm effective date for Czech outbound payments",
        "Document fallback domestic-law treatment",
    ],
    "pilot_structure_reconciliation": [
        "Reconcile pilot and global review-pack structures",
        "Confirm source-document identity",
        "Confirm treaty, protocol and MLI layering",
        "Resolve structural inconsistencies",
        "Document reusable global pattern",
    ],
    "protocol_effect_review": [
        "Confirm protocol identity and legal force",
        "Map amended treaty provisions",
        "Confirm entry into force and effective dates",
        "Validate dividend, interest and royalty impact",
        "Document unchanged provisions",
    ],
    "mli_ppt_and_effective_date_review": [
        "Confirm both jurisdictions' MLI positions",
        "Confirm covered tax agreement status",
        "Determine matching MLI provisions",
        "Confirm entry into effect for withholding taxes",
        "Assess PPT and other applicable overlays",
    ],
    "base_treaty_semantic_review": [
        "Confirm treaty identity and current applicability",
        "Review Articles 10, 11 and 12",
        "Confirm ownership or participation thresholds",
        "Confirm beneficial-owner conditions",
        "Confirm special exemptions and definitions",
    ],
}


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _scope_map() -> dict[str, dict[str, Any]]:
    payload = json.loads(
        WORKSTREAMS_PATH.read_text(
            encoding="utf-8"
        )
    )

    return {
        row["packet_id"]: row
        for row in payload["scopes"]
    }


def _review_tasks(
    workstreams: list[str],
) -> list[dict[str, Any]]:
    tasks = []

    for workstream in workstreams:
        requirements = REVIEW_REQUIREMENTS.get(
            workstream,
            [
                "Complete legal review",
                "Document evidence and conclusion",
            ],
        )

        tasks.append({
            "workstream": workstream,
            "requirements": requirements,
            "status": "not_started",
            "reviewer": None,
            "reviewed_at": None,
            "conclusion": None,
            "evidence_references": [],
        })

    return tasks


def build_execution_dossiers() -> dict[str, Any]:
    batches_payload = json.loads(
        BATCHES_PATH.read_text(
            encoding="utf-8"
        )
    )

    scopes = _scope_map()

    if len(scopes) != 300:
        raise ValueError(
            f"Expected 300 scopes, found {len(scopes)}."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dossiers = []

    for batch in batches_payload["batches"]:
        scope_rows = []

        for packet_id in batch["packet_ids"]:
            if packet_id not in scopes:
                raise ValueError(
                    f"{packet_id}: workstream scope missing."
                )

            scope = scopes[packet_id]

            scope_row = {
                "packet_id": packet_id,
                "recipient_country": (
                    scope["recipient_country"]
                ),
                "recipient_country_name": (
                    scope["recipient_country_name"]
                ),
                "income_type": (
                    scope["income_type"]
                ),
                "primary_review_workstream": (
                    scope[
                        "primary_review_workstream"
                    ]
                ),
                "review_workstreams": (
                    scope["review_workstreams"]
                ),
                "review_tasks": _review_tasks(
                    scope["review_workstreams"]
                ),
                "primary_review_status": (
                    "not_started"
                ),
                "independent_approval_status": (
                    "not_started"
                ),
                "approval_eligible": False,
                "promotable_to_active_rules": False,
                "source_workstream_sha256": (
                    scope["workstream_sha256"]
                ),
            }

            scope_row["scope_dossier_sha256"] = (
                _sha256_json(scope_row)
            )

            scope_rows.append(scope_row)

        dossier = {
            "schema_version": 1,
            "batch_id": batch["batch_id"],
            "batch_number": batch["batch_number"],
            "priority_tier": batch["priority_tier"],
            "countries": batch["countries"],
            "country_names": (
                batch["country_names"]
            ),
            "scope_count": len(scope_rows),
            "status": (
                "ready_for_primary_legal_review"
            ),
            "primary_reviewer": None,
            "independent_approver": None,
            "review_started_at": None,
            "review_completed_at": None,
            "approval_completed_at": None,
            "approval_eligible": False,
            "promotable_to_active_rules": False,
            "scope_dossiers": scope_rows,
            "batch_source_sha256": (
                batch["batch_sha256"]
            ),
        }

        dossier["dossier_sha256"] = (
            _sha256_json(dossier)
        )

        filename = (
            f"{batch['batch_id'].lower()}.json"
        )

        path = OUTPUT_DIR / filename

        path.write_text(
            json.dumps(
                dossier,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        dossiers.append({
            "batch_id": batch["batch_id"],
            "priority_tier": (
                batch["priority_tier"]
            ),
            "countries": batch["countries"],
            "scope_count": len(scope_rows),
            "status": dossier["status"],
            "file": filename,
            "dossier_sha256": (
                dossier["dossier_sha256"]
            ),
            "approval_eligible": False,
            "promotable_to_active_rules": False,
        })

    if len(dossiers) != 23:
        raise ValueError(
            f"Expected 23 dossiers, "
            f"found {len(dossiers)}."
        )

    if sum(
        row["scope_count"]
        for row in dossiers
    ) != 300:
        raise ValueError(
            "Execution dossiers do not cover "
            "all 300 scopes."
        )

    return {
        "schema_version": 1,
        "dataset_release": (
            "global-review-execution-dossiers-"
            "2026-08-06.1"
        ),
        "batch_count": len(dossiers),
        "scope_count": 300,
        "country_count": 100,
        "policy": {
            "fail_closed": True,
            "dossier_is_not_legal_approval":
                True,
            "human_primary_review_required":
                True,
            "independent_approval_required":
                True,
        },
        "dossiers": dossiers,
    }


def build_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_release": (
            payload["dataset_release"]
        ),
        "batch_count": payload["batch_count"],
        "scope_count": payload["scope_count"],
        "country_count": (
            payload["country_count"]
        ),
        "ready_for_primary_review_batches":
            sum(
                row["status"]
                == "ready_for_primary_legal_review"
                for row in payload["dossiers"]
            ),
        "approval_eligible_scopes": 0,
        "promotable_scopes": 0,
        "fail_closed": True,
    }


def main() -> None:
    payload = build_execution_dossiers()
    summary = build_summary(payload)

    INDEX_PATH.write_text(
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

    print("Dossiers:", payload["batch_count"])
    print("Scopes:", payload["scope_count"])
    print("Countries:", payload["country_count"])
    print(
        "Ready batches:",
        summary[
            "ready_for_primary_review_batches"
        ],
    )


if __name__ == "__main__":
    main()
