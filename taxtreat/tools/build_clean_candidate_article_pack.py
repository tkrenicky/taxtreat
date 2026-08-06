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

PACK_PATH = (
    REVIEW_ROOT
    / "clean_candidate_article_pack.json"
)

SUMMARY_PATH = (
    REVIEW_ROOT
    / "clean_candidate_article_pack_summary.json"
)

ARTICLE_NUMBERS = (10, 11, 12)


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


def article_hash(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def main() -> None:
    existing = read_json(PACK_PATH)
    rebuilt_rows = []

    for template in existing["treaty_partners"]:
        parsed_path = ROOT / template["parsed_path"]
        parsed = read_json(parsed_path)

        parsed_articles = {
            int(article["number"]): article
            for article in parsed["articles"]
        }

        articles = {}
        missing_articles = []
        empty_articles = []

        for number in ARTICLE_NUMBERS:
            source = parsed_articles.get(number)

            if source is None:
                missing_articles.append(number)
                continue

            text = str(source.get("text", ""))

            if not text.strip():
                empty_articles.append(number)

            source_index = next(
                (
                    index
                    for index, article in enumerate(
                        parsed["articles"]
                    )
                    if int(article["number"]) == number
                ),
                None,
            )

            articles[str(number)] = {
                "article_number": number,
                "title": source.get("title"),
                "text": text,
                "text_sha256": article_hash(text),
                "character_count": len(text),
                "source_index": source_index,
            }

        if missing_articles:
            extraction_status = (
                "article_mapping_incomplete"
            )
        elif empty_articles:
            extraction_status = "article_text_empty"
        else:
            extraction_status = (
                "candidate_articles_extracted"
            )

        row = dict(template)
        row.update(
            {
                "articles": articles,
                "missing_articles":
                    missing_articles,
                "empty_articles":
                    empty_articles,
                "extraction_status":
                    extraction_status,
                "required_review": True,
                "legal_text_verified": False,
                "production_ready": False,
                "fail_closed": True,
                "promotable_to_active_rules":
                    False,
            }
        )

        rebuilt_rows.append(row)

    rebuilt_rows.sort(
        key=lambda row: row["partner_country"]
    )

    status_counts = Counter(
        row["extraction_status"]
        for row in rebuilt_rows
    )

    payload = {
        "schema_version": 1,
        "dataset_release":
            "clean-candidate-article-pack-2026-08-06.2",
        "treaty_partner_count":
            len(rebuilt_rows),
        "article_scope_count":
            len(rebuilt_rows) * 3,
        "extraction_status_counts":
            dict(sorted(status_counts.items())),
        "review_semantics": {
            "parsed_text_is_authoritative": False,
            "article_extraction_is_legal_verification":
                False,
            "official_document_comparison_required":
                True,
            "protocol_and_mli_review_required": True,
            "unverified_result": "fail_closed",
        },
        "legal_verification_completed": False,
        "production_ready": False,
        "fail_closed": True,
        "promotable_to_active_rules": False,
        "treaty_partners": rebuilt_rows,
    }

    summary = {
        key: value
        for key, value in payload.items()
        if key != "treaty_partners"
    }

    write_json(PACK_PATH, payload)
    write_json(SUMMARY_PATH, summary)

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    for row in rebuilt_rows:
        print(
            row["treaty_pair_id"],
            row["extraction_status"],
            {
                number:
                    row["articles"][number][
                        "text_sha256"
                    ][:12]
                for number in row["articles"]
            },
        )


if __name__ == "__main__":
    main()
