from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

REVIEW_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

CLEAN_PACK = (
    REVIEW_ROOT
    / "clean_candidate_article_pack.json"
)

EVIDENCE_REGISTRY = (
    ROOT
    / "data"
    / "registries"
    / "legal_evidence_sources.json"
)

EVIDENCE_ARTIFACTS = (
    ROOT
    / "data"
    / "manifests"
    / "legal_evidence_artifacts.json"
)

OUTPUT = (
    REVIEW_ROOT
    / "clean_candidate_source_reconciliation.json"
)

SUMMARY_OUTPUT = (
    REVIEW_ROOT
    / "clean_candidate_source_reconciliation_summary.json"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def source_label(
    source: dict[str, Any],
) -> str | None:
    metadata = source.get("metadata") or {}

    for key in (
        "label",
        "source_title",
        "title",
    ):
        value = metadata.get(key)

        if isinstance(value, str):
            value = value.strip()

            if value:
                return value

    return None


def main() -> None:
    clean_pack = read_json(CLEAN_PACK)
    registry = read_json(EVIDENCE_REGISTRY)
    artifacts = read_json(EVIDENCE_ARTIFACTS)

    registry_by_label: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for source in registry["sources"]:
        label = source_label(source)

        if label:
            registry_by_label.setdefault(
                label,
                [],
            ).append(source)

    artifact_by_source_id = {
        artifact["source_id"]: artifact
        for artifact in artifacts["artifacts"]
    }

    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    hash_relation_counts: Counter[str] = Counter()

    for candidate in clean_pack[
        "treaty_partners"
    ]:
        title = candidate["source_title"]
        matching_sources = registry_by_label.get(
            title,
            [],
        )

        candidate_path = (
            ROOT / candidate["artifact_uri"]
        )

        candidate_file_exists = (
            candidate_path.is_file()
        )

        candidate_actual_sha256 = (
            file_sha256(candidate_path)
            if candidate_file_exists
            else None
        )

        candidate_hash_valid = (
            candidate_actual_sha256
            == candidate["artifact_sha256"]
            if candidate_actual_sha256
            else False
        )

        resolved_sources = []

        for source in matching_sources:
            artifact = artifact_by_source_id.get(
                source["source_id"]
            )

            if artifact is None:
                continue

            artifact_uri = artifact.get(
                "artifact_uri"
            )

            artifact_path = (
                ROOT / artifact_uri
                if artifact_uri
                else None
            )

            artifact_exists = bool(
                artifact_path
                and artifact_path.is_file()
            )

            artifact_actual_sha256 = (
                file_sha256(artifact_path)
                if artifact_exists
                else None
            )

            artifact_manifest_sha256 = (
                artifact.get("sha256")
            )

            artifact_hash_valid = bool(
                artifact_actual_sha256
                and artifact_actual_sha256
                == artifact_manifest_sha256
            )

            resolved_sources.append(
                {
                    "source_id":
                        source["source_id"],
                    "source_label": title,
                    "source_type": (
                        source.get("metadata")
                        or {}
                    ).get("source_type"),
                    "official_urls":
                        source.get(
                            "official_urls",
                            [],
                        ),
                    "artifact_status":
                        artifact.get("status"),
                    "artifact_uri":
                        artifact_uri,
                    "artifact_manifest_sha256":
                        artifact_manifest_sha256,
                    "artifact_actual_sha256":
                        artifact_actual_sha256,
                    "artifact_exists":
                        artifact_exists,
                    "artifact_hash_valid":
                        artifact_hash_valid,
                    "official_url":
                        artifact.get(
                            "official_url"
                        ),
                    "final_url":
                        artifact.get("final_url"),
                }
            )

        valid_official_sources = [
            source
            for source in resolved_sources
            if source["artifact_status"]
            in {
                "verified_pdf",
                "existing_verified_artifact",
            }
            and source["artifact_hash_valid"]
        ]

        official_hashes = sorted({
            source[
                "artifact_actual_sha256"
            ]
            for source in valid_official_sources
            if source[
                "artifact_actual_sha256"
            ]
        })

        if not matching_sources:
            reconciliation_status = (
                "official_registry_match_missing"
            )
            hash_relation = "not_comparable"
        elif not resolved_sources:
            reconciliation_status = (
                "official_artifact_record_missing"
            )
            hash_relation = "not_comparable"
        elif not valid_official_sources:
            reconciliation_status = (
                "official_artifact_not_locally_verified"
            )
            hash_relation = "not_comparable"
        elif not candidate_hash_valid:
            reconciliation_status = (
                "candidate_artifact_hash_invalid"
            )
            hash_relation = "not_comparable"
        elif candidate_actual_sha256 in official_hashes:
            reconciliation_status = (
                "candidate_matches_official_artifact"
            )
            hash_relation = "identical"
        else:
            reconciliation_status = (
                "candidate_differs_from_official_artifact"
            )
            hash_relation = "different"

        status_counts[
            reconciliation_status
        ] += 1

        hash_relation_counts[
            hash_relation
        ] += 1

        requires_fresh_extraction = (
            reconciliation_status
            != "candidate_matches_official_artifact"
        )

        rows.append(
            {
                "treaty_pair_id":
                    candidate["treaty_pair_id"],
                "partner_country":
                    candidate["partner_country"],
                "partner_country_name":
                    candidate[
                        "partner_country_name"
                    ],
                "source_title": title,
                "candidate_source_id":
                    candidate["source_id"],
                "candidate_artifact_uri":
                    candidate["artifact_uri"],
                "candidate_manifest_sha256":
                    candidate[
                        "artifact_sha256"
                    ],
                "candidate_actual_sha256":
                    candidate_actual_sha256,
                "candidate_artifact_exists":
                    candidate_file_exists,
                "candidate_hash_valid":
                    candidate_hash_valid,
                "candidate_article_hashes": {
                    number: article[
                        "text_sha256"
                    ]
                    for number, article
                    in candidate[
                        "articles"
                    ].items()
                },
                "official_registry_match_count":
                    len(matching_sources),
                "official_artifact_match_count":
                    len(resolved_sources),
                "valid_official_artifact_count":
                    len(valid_official_sources),
                "valid_official_artifact_hashes":
                    official_hashes,
                "official_sources":
                    resolved_sources,
                "hash_relation":
                    hash_relation,
                "reconciliation_status":
                    reconciliation_status,
                "requires_fresh_official_extraction":
                    requires_fresh_extraction,
                "existing_article_extraction_reusable":
                    not requires_fresh_extraction,
                "official_source_identity_verified":
                    False,
                "official_document_content_verified":
                    False,
                "articles_10_12_legally_verified":
                    False,
                "production_ready":
                    False,
                "fail_closed":
                    True,
                "promotable_to_active_rules":
                    False,
            }
        )

    rows.sort(
        key=lambda row: row[
            "partner_country"
        ]
    )

    payload = {
        "schema_version": 1,
        "dataset_release":
            "clean-candidate-source-reconciliation-2026-08-06.1",
        "clean_candidate_pack_release":
            clean_pack["dataset_release"],
        "legal_evidence_registry_release":
            registry["dataset_release"],
        "legal_evidence_artifact_release":
            artifacts["dataset_release"],
        "treaty_partner_count": len(rows),
        "reconciliation_status_counts":
            dict(sorted(
                status_counts.items()
            )),
        "hash_relation_counts":
            dict(sorted(
                hash_relation_counts.items()
            )),
        "treaty_partners": rows,
        "semantics": {
            "matching_hash_proves_file_identity_only":
                True,
            "matching_hash_is_legal_verification":
                False,
            "different_hash_requires_fresh_extraction":
                True,
            "official_article_comparison_required":
                True,
            "protocol_and_mli_review_required":
                True,
            "automatic_production_promotion_allowed":
                False,
            "unverified_result": "fail_closed",
        },
        "legal_verification_completed": False,
        "production_ready": False,
        "fail_closed": True,
        "promotable_to_active_rules": False,
    }

    summary = {
        key: value
        for key, value in payload.items()
        if key != "treaty_partners"
    }

    write_json(OUTPUT, payload)
    write_json(SUMMARY_OUTPUT, summary)

    print(json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
    ))

    print("\nPartner results:")

    for row in rows:
        print(
            row["treaty_pair_id"],
            row["reconciliation_status"],
            row["hash_relation"],
        )


if __name__ == "__main__":
    main()
