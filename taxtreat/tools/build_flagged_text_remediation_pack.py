from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REVIEW_ROOT = (
    ROOT
    / "data"
    / "legal_reviews"
    / "global_cz_outbound"
)

AUDIT_PATH = (
    REVIEW_ROOT
    / "clean_candidate_text_quality_audit.json"
)

OUTPUT_PATH = (
    REVIEW_ROOT
    / "flagged_text_remediation_pack.json"
)

SUMMARY_PATH = (
    REVIEW_ROOT
    / "flagged_text_remediation_pack_summary.json"
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


def build_pack(
    audit: dict[str, Any],
) -> dict[str, Any]:
    flagged_partners = []

    for partner in audit["treaty_partners"]:
        if (
            partner["quality_status"]
            == "automated_quality_gate_passed"
        ):
            continue

        articles = []

        for article_number, article in sorted(
            partner["article_results"].items(),
            key=lambda item: int(item[0]),
        ):
            if not article["findings"]:
                continue

            articles.append(
                {
                    "article_number":
                        int(article_number),
                    "article_title":
                        article["title"],
                    "current_text_sha256":
                        article["text_sha256"],
                    "error_count":
                        article["error_count"],
                    "warning_count":
                        article["warning_count"],
                    "findings":
                        article["findings"],
                    "required_action":
                        "compare_with_official_artifact",
                    "corrected_text": None,
                    "corrected_text_sha256": None,
                    "comparison_completed": False,
                    "clean_text_verified": False,
                    "legal_text_verified": False,
                }
            )

        flagged_partners.append(
            {
                "treaty_pair_id":
                    partner["treaty_pair_id"],
                "partner_country":
                    partner["partner_country"],
                "partner_country_name":
                    partner[
                        "partner_country_name"
                    ],
                "source_title":
                    partner["source_title"],
                "quality_status":
                    partner["quality_status"],
                "total_error_count":
                    partner["error_count"],
                "total_warning_count":
                    partner["warning_count"],
                "articles": articles,
                "remediation_status":
                    "official_comparison_required",
                "production_ready": False,
                "fail_closed": True,
            }
        )

    flagged_partners.sort(
        key=lambda row: row["partner_country"]
    )

    finding_count = sum(
        len(article["findings"])
        for partner in flagged_partners
        for article in partner["articles"]
    )

    article_scope_count = sum(
        len(partner["articles"])
        for partner in flagged_partners
    )

    return {
        "schema_version": 2,
        "dataset_release":
            "flagged-text-remediation-pack-2026-08-06.2",
        "source_audit_release":
            audit["dataset_release"],
        "treaty_partner_count":
            len(flagged_partners),
        "article_scope_count":
            article_scope_count,
        "finding_count":
            finding_count,
        "treaty_partners":
            flagged_partners,
        "semantics": {
            "finding_is_legal_conclusion": False,
            "automatic_text_replacement_allowed":
                False,
            "official_document_comparison_required":
                True,
            "corrected_text_requires_new_hash":
                True,
            "automated_quality_pass_is_verification":
                False,
            "unresolved_result": "fail_closed",
        },
        "clean_text_verification_completed":
            False,
        "legal_verification_completed": False,
        "production_ready": False,
        "fail_closed": True,
        "promotable_to_active_rules": False,
    }


def main() -> None:
    audit = read_json(AUDIT_PATH)
    payload = build_pack(audit)

    summary = {
        key: value
        for key, value in payload.items()
        if key != "treaty_partners"
    }

    write_json(OUTPUT_PATH, payload)
    write_json(SUMMARY_PATH, summary)

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nFlagged partners:")

    for partner in payload["treaty_partners"]:
        print(
            partner["treaty_pair_id"],
            partner["partner_country_name"],
            partner["quality_status"],
            f"errors={partner['total_error_count']}",
            f"warnings={partner['total_warning_count']}",
        )

        for article in partner["articles"]:
            for finding in article["findings"]:
                print(
                    f"  Article "
                    f"{article['article_number']}",
                    finding["severity"],
                    finding["code"],
                    "=>",
                    finding["excerpt"],
                )


if __name__ == "__main__":
    main()
