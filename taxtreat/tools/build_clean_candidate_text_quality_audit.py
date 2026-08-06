from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from taxtreat.validation.legal_text_quality import (
    quality_result,
)


ROOT = Path(__file__).resolve().parents[2]

REVIEW_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

INPUT = (
    REVIEW_ROOT
    / "clean_candidate_article_pack.json"
)

RECONCILIATION = (
    REVIEW_ROOT
    / "clean_candidate_source_reconciliation.json"
)

OUTPUT = (
    REVIEW_ROOT
    / "clean_candidate_text_quality_audit.json"
)

SUMMARY_OUTPUT = (
    REVIEW_ROOT
    / "clean_candidate_text_quality_audit_summary.json"
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


def main() -> None:
    article_pack = read_json(INPUT)
    reconciliation = read_json(RECONCILIATION)

    reconciliation_by_pair = {
        row["treaty_pair_id"]: row
        for row in reconciliation[
            "treaty_partners"
        ]
    }

    rows = []
    partner_status_counts = Counter()
    finding_code_counts = Counter()

    for partner in article_pack[
        "treaty_partners"
    ]:
        pair_id = partner["treaty_pair_id"]
        source_match = reconciliation_by_pair[
            pair_id
        ]

        article_results = {}

        for number in ("10", "11", "12"):
            article = partner["articles"][number]
            result = quality_result(
                article["text"]
            )

            article_results[number] = {
                "article_number": int(number),
                "title": article["title"],
                "text_sha256":
                    article["text_sha256"],
                **result,
            }

            for finding in result["findings"]:
                finding_code_counts[
                    finding["code"]
                ] += 1

        error_count = sum(
            article["error_count"]
            for article in article_results.values()
        )

        warning_count = sum(
            article["warning_count"]
            for article in article_results.values()
        )

        if error_count:
            status = (
                "text_remediation_required"
            )
        elif warning_count:
            status = (
                "manual_text_review_required"
            )
        else:
            status = (
                "automated_quality_gate_passed"
            )

        partner_status_counts[status] += 1

        rows.append(
            {
                "treaty_pair_id": pair_id,
                "partner_country":
                    partner["partner_country"],
                "partner_country_name":
                    partner[
                        "partner_country_name"
                    ],
                "source_title":
                    partner["source_title"],
                "official_artifact_identical":
                    source_match[
                        "hash_relation"
                    ] == "identical",
                "article_results":
                    article_results,
                "error_count": error_count,
                "warning_count": warning_count,
                "quality_status": status,
                "automated_quality_gate_passed":
                    error_count == 0,
                "clean_text_verified": False,
                "articles_10_12_legally_verified":
                    False,
                "production_ready": False,
                "fail_closed": True,
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
            "clean-candidate-text-quality-audit-2026-08-06.1",
        "article_pack_release":
            article_pack["dataset_release"],
        "source_reconciliation_release":
            reconciliation[
                "dataset_release"
            ],
        "treaty_partner_count": len(rows),
        "article_scope_count": len(rows) * 3,
        "partner_status_counts":
            dict(sorted(
                partner_status_counts.items()
            )),
        "finding_code_counts":
            dict(sorted(
                finding_code_counts.items()
            )),
        "treaty_partners": rows,
        "semantics": {
            "automated_quality_check_is_legal_verification":
                False,
            "zero_detected_errors_proves_perfect_text":
                False,
            "manual_comparison_with_official_document_required":
                True,
            "detected_error_result":
                "fail_closed",
            "automatic_production_promotion_allowed":
                False,
        },
        "clean_text_verification_completed":
            False,
        "legal_verification_completed":
            False,
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
            row["quality_status"],
            f"errors={row['error_count']}",
            f"warnings={row['warning_count']}",
        )


if __name__ == "__main__":
    main()
